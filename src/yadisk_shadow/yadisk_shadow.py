__version__ = 'v0.9.0'
__bugtracker__ = 'https://github.com/regnveig/yadisk-shadow/issues'

import argparse
import json
import logging
import os
import requests #
import sys
import time
import tqdm #

LIMIT = int(100)
TIMEOUT = int(10)
WAIT = int(5)
MAXTRIES = int(3)
METHODS = ['metadata', 'download']
CHUNKSIZE = int(1024)

logging.basicConfig(format = '[%(levelname)s] %(message)s', level = logging.INFO)

def ArmoredRequest(Link):
	logging.info(f'GET Request: {Link}')
	Tried = 0
	while True:
		try:
			Response = requests.get(Link, timeout = TIMEOUT)
			break
		except Exception as Err:
			Tried += 1
			logging.warning(f'Request error [try {str(Tried)}]: {Err}')
			if (Tried == MAXTRIES):
				logging.error(f'Cannot perform request. Exit.')
				exit(1)
		time.sleep(WAIT)
	try:
		Data = Response.json()
	except requests.exceptions.JSONDecodeError:
		logging.error(f'Invalid JSON response')
		exit(1)
	if 'error' in Data:
		logging.error(f'{Data["error"]}: {Data["description"]} ({Data["message"]})')
		exit(1)
	return Data

def ArmoredDownload(Name, Link, Path, Total):
	Tried = 0
	while True:
		try:
			Stream = requests.get(Link, stream = True, timeout = TIMEOUT)
			break
		except Exception as Err:
			Tried += 1
			logging.warning(f'Request error [try {str(Tried)}]: {Err}')
			if (Tried == MAXTRIES):
				logging.error(f'Cannot perform request. Exit.')
				exit(1)
		time.sleep(WAIT)
	Stream.raise_for_status()
	Output = open(Path, 'wb')
	for Chunk in tqdm.tqdm(Stream.iter_content(chunk_size = CHUNKSIZE), total = int(Total / CHUNKSIZE), desc = Name, unit = 'kb'):
		Output.write(Chunk)

def RenderArguments(Args):
	KeyValue = list()
	for Key, Value in Args.items(): KeyValue.append(f'{Key}={Value}')
	return '&'.join(KeyValue)

def GetTree(Link, Path = '/'):
	Files = list()
	Offset = 0
	while True:
		Args = {
			'path': Path,
			'limit': str(LIMIT),
			'offset': str(Offset),
			'public_key': Link
			}
		RenderedArgs = RenderArguments(Args)
		Data = ArmoredRequest(f'https://cloud-api.yandex.net/v1/disk/public/resources?{RenderedArgs}')
		if (not Data['_embedded']['items']): break
		for Item in Data['_embedded']['items']:
			if Item['type'] == 'file': Files.append(Item)
			elif Item['type'] == 'dir': Files.extend(GetTree(Link, Item['path']))
		Offset += LIMIT
		time.sleep(WAIT)
	return Files

def DownloadTree(MetaJSON, RootDirectory):
	with open(MetaJSON, 'rt') as Meta: Metadata = json.load(Meta)
	try:
		os.mkdir(RootDirectory)
	except FileExistsError:
		logging.error(f'Output dir already exists!')
		exit(1)
	RealRoot = os.path.realpath(RootDirectory)
	for Item in Metadata:
		RealPath = os.path.join(RealRoot, Item['path'][1:])
		os.makedirs(os.path.dirname(RealPath), exist_ok = True)
		ArmoredDownload(Item['name'], Item['file'], RealPath, Item['size'])

def CreateParser():
	Parser = argparse.ArgumentParser(
		formatter_class = argparse.RawDescriptionHelpFormatter,
		description = f'yadisk-shadow {__version__}: Download shared Yandex.Disk folders metadata and files',
		epilog = f'Bug tracker: {__bugtracker__}')

	Parser.add_argument('-v', '--version', action = 'version', version = __version__)
	Subparsers = Parser.add_subparsers(title = 'Commands', dest = 'command')

	MetadataParser = Subparsers.add_parser('Metadata', help = f'Get shared folder tree metadata')
	MetadataParser.add_argument('-l', '--link', required = True, type = str, help = f'Ya.Disk shared folder link')
	MetadataParser.add_argument('-o', '--output', required = True, type = str, help = f'Metadata JSON file')
	MetadataParser.add_argument('-s', '--subdir', default = '/', type = str, help = f'Subdirectory, prepended with /')

	DownloadParser = Subparsers.add_parser('Download', help = f'Download shared files listed in Metadata JSON file')
	DownloadParser.add_argument('-m', '--meta', required = True, type = str, help = f'Metadata JSON file')
	DownloadParser.add_argument('-d', '--dir', required = True, type = str, help = f'Root directory for the tree to download')
	return Parser

def main():
	Parser = CreateParser()
	Namespace = Parser.parse_args(sys.argv[1:])
	if Namespace.command == 'Metadata':
		Files = GetTree(Namespace.link, Namespace.subdir)
		with open(Namespace.output, 'wt') as Output: json.dump(Files, Output, ensure_ascii = False, indent = 4)
	elif Namespace.command == 'Download':
		DownloadTree(Namespace.meta, Namespace.dir)
	else: Parser.print_help()

if __name__ == '__main__': main()
