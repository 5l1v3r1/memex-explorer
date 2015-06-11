from __future__ import unicode_literals

import os
import shutil

# Test
from memex.test_utils.unit_test_utils import UnitTestSkeleton, form_errors, get_object
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest

# App
from apps.crawl_space.forms import AddCrawlForm
from apps.crawl_space.models import Crawl, CrawlModel
from base.models import Project, alphanumeric_validator


def assert_form_errors(response, *errors):
    """Given a response, assert that only the given `errors`
    are present in the form response."""

    efe = expected_form_errors = set(errors)
    assert set(form_errors(response).keys()) - efe == set()


class TestViews(UnitTestSkeleton):

    @classmethod
    def setUpClass(cls):
        """Initialize a test project and crawl model,
        and save them to the test database."""
        super(TestViews, cls).setUpClass()

        cls.test_project = Project(
            name = "Test",
            description = "Test Project Description")
        cls.test_project.save()

        cls.test_crawl = Crawl(
            name = "Test Crawl",
            description = "Test Crawl Description",
            crawler = "nutch",
            config = "config_default",
            seeds_list = cls.get_seeds(),
            project = cls.test_project
        )
        cls.test_crawl.save()

        cls.test_crawlmodel = CrawlModel(
            name = "Test Crawl Model",
            model = cls.get_model_file(),
            features = cls.get_features_file(),
            project = cls.test_project,
        )
        cls.test_crawlmodel.save()

    @classmethod
    def get_model_file(self):
        return SimpleUploadedFile('pageclassifier.model', bytes('This is a model file.\n'), 'utf-8')

    @classmethod
    def get_features_file(self):
        return SimpleUploadedFile('pageclassifier.features', bytes('This is a features file.\n'), 'utf-8')

    @classmethod
    def get_seeds(self):
        """Return a new instance of SimpleUploadedFile. This file can only
        be used once."""

        return SimpleUploadedFile('ht.seeds', bytes('This is some content.\n'), 'utf-8')

    @property
    def form_data(self):
        """Provide a dictionary of valid form data."""
        return {
            'name': 'Cat Crawl',
            'description': 'Find all the cats.',
            'crawler': 'ache',
            'seeds_list': self.get_seeds(),
            'crawl_model': self.test_crawlmodel.pk,
        }

    @property
    def slugs(self):
        """Return a dictionary with a "test" project slug."""

        return dict(slugs=dict(
            project_slug="test"))

    @property
    def crawl_slugs(self):
        """Return a dictionary with a "test" project slug and
        a "test-crawl" crawl slug."""

        return dict(slugs=dict(
            project_slug="test",
            crawl_slug="test-crawl"))

    @property
    def cat_slugs(self):
        """Return a dictionary with a "test" project slug and
        a "test-crawl" crawl slug."""

        return dict(slugs=dict(
            project_slug="test",
            crawl_slug="cat-crawl"))

    def test_add_crawl_page(self):
        """Get the add_crawl page with **self.slugs and assert that
        the right template is returned."""

        response = self.get('base:crawl_space:add_crawl', **self.slugs)
        assert 'crawl_space/add_crawl.html' in response.template_name

    def test_add_crawl_no_data(self):
        """Post with an empty form, assert that each of the missings fields
        prompts an error."""

        response = self.post('base:crawl_space:add_crawl', **self.slugs)
        assert_form_errors(response, *self.form_data.keys())

    def test_add_crawl_bad_name(self):
        """Post with a non-alphanumeric name."""

        import re

        form_data = self.form_data
        form_data['name'] = bad_name = "lEe8$|>EE|<"
        validator = alphanumeric_validator()
        assert re.match(validator.regex, bad_name) is None

        response = self.post('base:crawl_space:add_crawl',
            form_data, **self.slugs)
        assert_form_errors(response, 'name')

    def test_add_crawl_bad_crawler(self):
        """Post with an invalid crawler."""

        form_data = self.form_data
        form_data['crawler'] = "error"

        response = self.post('base:crawl_space:add_crawl',
            form_data, **self.slugs)
        assert_form_errors(response, 'crawl_model', 'crawler')

    def test_add_crawl_success(self):
        """Post with a valid form payload, and assert that
        the client is redirected to the appropriate crawl page."""
        response = self.post('base:crawl_space:add_crawl',
            self.form_data,
            **self.slugs)
        assert 'crawl_space/crawl.html' in response.template_name

    @pytest.mark.xfail
    def test_crawl_page(self):
        # Get the test crawl page, and assert that the
        # crawl slug is generated properly and the project
        # is linked correctly.
        response = self.get('base:crawl_space:crawl', **self.crawl_slugs)
        assert 'crawl_space/crawl.html' in response.template_name

        crawl = get_object(response)
        assert (crawl.name, crawl.slug) == ("Test Crawl", "test-crawl")
        assert crawl.project == self.test_project

    def test_crawl_settings_page(self):
        response = self.get('base:crawl_space:crawl_settings', **self.crawl_slugs)
        assert 'crawl_space/crawl_update_form.html' in response.template_name

    @pytest.mark.xfail
    def test_crawl_settings_change_name(self):
        response = self.post('base:crawl_space:crawl_settings',
            {'name': 'Dog Crawl'}, **self.crawl_slugs)
        crawl = get_object(response)
        assert crawl.name == "Cat Crawl"

    def test_crawl_settings_change_description(self):
        response = self.post('base:crawl_space:crawl_settings',
            {'description': 'A crawl for information about cats.'},
            **self.crawl_slugs)
        crawl = get_object(response)
        assert crawl.description == "A crawl for information about cats." 

    def test_crawl_delete(self):
        response = self.post('base:crawl_space:delete_crawl',
            **self.crawl_slugs)
        assert 'base/project.html' in response.template_name
