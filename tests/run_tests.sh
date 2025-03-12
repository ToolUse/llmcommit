#!/bin/bash
# Helper script to run tests with coverage

# Ensure we're in the project root directory
cd "$(dirname "$0")/.."

# Colors for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running tests with coverage...${NC}"

# Check if pytest-cov and pytest-timeout are installed
if ! python -c "import pytest_cov" 2>/dev/null; then
    echo "Installing pytest-cov..."
    uv pip install pytest-cov
fi

if ! python -c "import pytest_timeout" 2>/dev/null; then
    echo "Installing pytest-timeout..."
    uv pip install pytest-timeout
fi

# Create or update pytest.ini to ensure non-interactive tests
cat > pytest.ini << EOF
[pytest]
# Fail tests immediately if they try to get user input
mock_use_standalone_module = true
# Show more details about test failures
addopts = -v
# Timeout after 5 seconds (to prevent hanging on user input)
timeout = 5
EOF

# Run tests with coverage and generate HTML report
# Set PYTHONPATH to ensure blueprint module can be found
PYTHONPATH=./src python -m pytest tests/ --cov=blueprint --cov-report=term --cov-report=html

# Check exit status
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests passed!${NC}"
    echo -e "HTML coverage report generated in htmlcov/"
    
    # Open coverage report on macOS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        open htmlcov/index.html
    fi
else
    echo -e "${RED}Tests failed.${NC}"
    echo -e "${YELLOW}If tests are hanging or asking for input, check for non-mocked interactive components.${NC}"
fi 