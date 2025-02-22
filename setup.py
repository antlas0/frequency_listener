from setuptools import setup, find_packages

# Function to read the requirements.txt file


def parse_requirements(filename):
    with open(filename, 'r') as file:
        lines = file.read().splitlines()
        # Filter out comments and empty lines
        requirements = [
            line for line in lines if line and not line.startswith('#')]
    return requirements


# Parse requirements.txt
requirements = parse_requirements('requirements.txt')

setup(
    name="frequency_listener",
    version="0.0.1",
    packages=find_packages(),
    install_requires=requirements,
    author="antlas0",
)
