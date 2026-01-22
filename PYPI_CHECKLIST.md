# PyPI Publication Checklist

This checklist ensures the package is ready for publication to PyPI.

## ✓ Package Structure

- [x] Package name: `itl-kubectl-oidc-setup`
- [x] Version defined in `__init__.py`: `1.0.0`
- [x] `setup.py` configured correctly
- [x] `pyproject.toml` configured correctly
- [x] `MANIFEST.in` includes necessary files
- [x] `LICENSE` file present (MIT)
- [x] `README.md` with clear description
- [x] `.gitignore` configured

## ✓ Package Contents

- [x] Main module: `itl_kubectl_oidc_setup/__init__.py`
- [x] Entry point: `itl_kubectl_oidc_setup/__main__.py`
- [x] Console script entry point defined
- [x] Dependencies specified in `pyproject.toml`
- [x] Dev dependencies specified

## ✓ Build & Test

- [x] Package builds successfully (`python -m build`)
- [x] Package installs successfully
- [x] Command runs: `itl-kubectl-oidc-setup --version`
- [x] Command executes main functionality
- [ ] All tests pass (`pytest`)
- [ ] Linting passes (`flake8`)
- [ ] Type checking passes (`mypy`)

## ✓ Documentation

- [x] README.md with badges
- [x] Installation instructions
- [x] Usage examples
- [x] Quick start guide (QUICKSTART.md)
- [x] Detailed installation guide
- [x] Troubleshooting guide
- [x] API/Command documentation

## ✓ Installation Methods

- [x] pip install
- [x] Zero-click bash installer (install.sh)
- [x] Zero-click PowerShell installer (install.ps1)
- [x] From source
- [x] Verification script (verify-install.py)

## ✓ CI/CD

- [x] GitHub Actions workflow configured
- [x] Tests run on push/PR
- [x] Multi-platform testing (Linux, macOS, Windows)
- [x] Multi-Python version testing (3.8-3.12)
- [x] Build artifacts generated
- [x] PyPI publish workflow configured

## ⚠️ Required for PyPI Publication

- [ ] **PyPI account created**
- [ ] **Test PyPI account created** (recommended for testing)
- [ ] **PyPI API token generated**
- [ ] **Test PyPI API token generated**
- [ ] **GitHub secrets configured:**
  - `PYPI_API_TOKEN`
  - `TEST_PYPI_API_TOKEN`
- [ ] **Package name available on PyPI**
- [ ] **Test upload to Test PyPI**
- [ ] **Verify test installation:** `pip install -i https://test.pypi.org/simple/ itl-kubectl-oidc-setup`

## 📦 Publication Commands

### Test PyPI (Recommended First)

```bash
# Clean previous builds
make clean

# Build package
python -m build

# Check package
twine check dist/*

# Upload to Test PyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ itl-kubectl-oidc-setup
```

### Production PyPI

```bash
# Clean previous builds
make clean

# Build package
python -m build

# Check package
twine check dist/*

# Upload to PyPI
python -m twine upload dist/*

# Verify
pip install itl-kubectl-oidc-setup
```

## 🔄 Version Management

For new releases:

1. Update version in `itl_kubectl_oidc_setup/__init__.py`
2. Update CHANGELOG (if exists)
3. Commit changes
4. Create git tag: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. GitHub Actions will automatically publish (if configured)

Or manually:
```bash
make release  # Builds and uploads to PyPI
```

## 🧪 Testing After Publication

After publishing to PyPI:

```bash
# Create test environment
python -m venv test-env
source test-env/bin/activate  # On Windows: test-env\Scripts\activate

# Install from PyPI
pip install itl-kubectl-oidc-setup

# Test
itl-kubectl-oidc-setup --version
itl-kubectl-oidc-setup --help

# Test zero-click installers
curl -fsSL https://raw.githubusercontent.com/ITlusions/ITLAuth/main/install.sh | bash

# Cleanup
deactivate
rm -rf test-env
```

## 📝 Post-Publication Tasks

- [ ] Update README with correct PyPI badge
- [ ] Announce release on GitHub Discussions
- [ ] Update documentation with correct version numbers
- [ ] Create GitHub Release with changelog
- [ ] Update related projects that depend on this package
- [ ] Verify all documentation links work

## 🔗 Useful Links

- **PyPI Project:** https://pypi.org/project/itl-kubectl-oidc-setup/
- **Test PyPI Project:** https://test.pypi.org/project/itl-kubectl-oidc-setup/
- **GitHub Repository:** https://github.com/ITlusions/ITLAuth
- **Documentation:** https://github.com/ITlusions/ITLAuth/tree/main/docs

## ⚡ Quick Commands Reference

```bash
# Build
make build

# Test upload
make upload-test

# Production upload
make upload

# Complete release
make release

# Run tests
make test

# Lint
make lint

# Format
make format
```

## 🎉 Success Criteria

Package is ready for publication when:

- ✅ All required checklist items are complete
- ✅ Package builds without errors
- ✅ Package installs successfully
- ✅ Command executes correctly
- ✅ Documentation is clear and accurate
- ✅ Tests pass (if present)
- ✅ Zero-click installers work
- ✅ Test PyPI upload succeeded
- ✅ Test PyPI installation verified

---

Last updated: 2026-01-22
Version: 1.0.0
