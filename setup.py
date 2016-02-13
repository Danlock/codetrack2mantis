from setuptools import setup, find_packages

setup(
	name = 'Codetrack2Mantis',
	version = '2.1',
	packages = ['Codetrack2Mantis','Codetrack2Mantis.res','Codetrack2Mantis.res.dateutil'],
	author = 'Daniel Lockhart',
	author_email = 'daniel.lockhart@mathresources.com',
	url = 'letsdomath.com',
	description = 'Converts Codetrack xml exported issue files into Mants issue xml files, and optionally uploads them into Mantis.',

	)