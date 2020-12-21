from setuptools import find_packages, setup

setup(
    name='WeatherApplication',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'flask',
        'geopy',
        'requests',
        'flask-bootstrap',
        'python-dotenv'
    ],
)

