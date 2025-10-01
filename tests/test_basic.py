"""
Test suite for itl-kubectl-oidc-setup package
"""

import unittest
import sys
import os

# Add the package to the path for testing
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from itl_kubectl_oidc_setup import __version__


class TestPackage(unittest.TestCase):
    """Test basic package functionality"""
    
    def test_version_exists(self):
        """Test that version is defined"""
        self.assertIsNotNone(__version__)
        self.assertIsInstance(__version__, str)
        self.assertTrue(len(__version__) > 0)
    
    def test_version_format(self):
        """Test that version follows semantic versioning"""
        parts = __version__.split('.')
        self.assertGreaterEqual(len(parts), 2)
        self.assertLessEqual(len(parts), 4)
        
        # Test that major and minor are integers
        self.assertTrue(parts[0].isdigit())
        self.assertTrue(parts[1].isdigit())


class TestKubectlOIDCSetup(unittest.TestCase):
    """Test KubectlOIDCSetup class functionality"""
    
    def test_import(self):
        """Test that we can import the main class"""
        try:
            from itl_kubectl_oidc_setup.__main__ import KubectlOIDCSetup
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import KubectlOIDCSetup: {e}")
    
    def test_class_instantiation(self):
        """Test that we can create an instance of KubectlOIDCSetup"""
        try:
            from itl_kubectl_oidc_setup.__main__ import KubectlOIDCSetup
            setup = KubectlOIDCSetup()
            self.assertIsNotNone(setup)
            # Test that the class has expected methods
            self.assertTrue(hasattr(setup, 'run'))
            self.assertTrue(callable(getattr(setup, 'run')))
        except Exception as e:
            self.fail(f"Failed to instantiate KubectlOIDCSetup: {e}")


if __name__ == '__main__':
    unittest.main()