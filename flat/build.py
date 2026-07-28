from os import chdir, linesep, makedirs, sep, walk
from os.path import abspath, basename, dirname, isdir, isfile, islink, join, relpath, split, splitext
from shutil import copy, copytree
from sys import argv, exit
from base64 import b64decode, urlsafe_b64decode
from json import loads
from re import search
from subprocess import TimeoutExpired, run
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)
try:
	chdir(abspath(dirname(__file__)))
except:
	pass


class JSONLoader:
	__DefaultEncoding = "utf-8"
	@staticmethod
	def load(JSONFilePath:str) -> object:
		try:
			with open(JSONFilePath, "rb") as f:
				raw = f.read()
			pureASCII = raw.decode("ascii", errors = "ignore")
			matches = search("^\t\"encoding\"\\s*:\\s*\"([^\"]*)\"", pureASCII)
			encoding = matches.group(1) if matches else JSONLoader.__DefaultEncoding
			with open(JSONFilePath, "r", encoding = encoding) as f:
				content = f.read()
			return loads(content)
		except Exception as e:
			return e

class Builder:
	__DefaultMetadataFilePath = "metadata.json"
	__Templates = None
	__DefaultTargetFileName = "main.tex"
	__DefaultEncoding = "utf-8"
	__Engines = ("tex", "latex", "luatex", "lualatex", "ptex", "platex", "pdftex", "pdflatex", "uptex", "uplatex", "xetex", "xelatex")
	__DefaultEngine = "pdflatex"
	__DefaultCompilationTimeout = 10
	def __init__(self:object, metadataFilePath:str = __DefaultMetadataFilePath) -> object:
		try:
			self.__metadataFilePath = str(metadataFilePath)
		except:
			self.__metadataFilePath = Builder.__DefaultMetadataFilePath
	def build(self:object) -> dict:
		diagnostics = {"succeeded":[], "failed":{}, "skipped":[], "mismatched":0, "aborted":None}
		try:
			if Builder.__Templates is None:
				Builder.__Templates = __import__("templates").Templates
			dictionary = JSONLoader.load(self.__metadataFilePath)
			for target in dictionary["targets"]:
				if (
					isinstance(target, dict) and "output" in target and "template" in target and isinstance(target["output"], dict)
					and "path" in target["output"] and isinstance(target["output"]["path"], str)
					and isinstance(target["template"], dict) and "category" in target["template"] and isinstance(target["template"]["category"], str)
					and "name" in target["template"] and isinstance(target["template"]["name"], str)
					and hasattr(Builder.__Templates, target["template"]["name"]) and hasattr(getattr(Builder.__Templates, target["template"]["name"]), target["template"]["category"])
				):
					identifier = "{0}.{1}".format(target["template"]["name"], target["template"]["category"]) # fetch a unique identifier like "IEEE.Journals"
					if identifier in diagnostics["succeeded"] or identifier in diagnostics["failed"]:
						diagnostics["skipped"].append(identifier)
					else:
						try:
							# Generate #
							targetFilePath = join(target["output"]["path"], Builder.__DefaultTargetFileName) if (
								target["output"]["path"].endswith((sep, "/")) or target["output"].get("type", "file") == "directory"
							) else target["output"]["path"]
							targetDirectoryPath, targetFileName = split(targetFilePath)
							if targetDirectoryPath:
								makedirs(targetDirectoryPath, exist_ok = True)
							encoding = target["output"].get("encoding", Builder.__DefaultEncoding)
							newline = {"cr":"\r", "crlf":"\r\n", "lf":"\n", "macintosh":"\r", "unix":"\n", "windows":"\r\n"}.get(
								target["output"].get("newline", "auto").lower(), linesep
							)
							for key, value in getattr(getattr(Builder.__Templates, target["template"]["name"]), target["template"]["category"]).format(
								dirname(self.__metadataFilePath), targetFileName, abstract = dictionary.get("abstract"), authors = dictionary.get("authors"), 
								keywords = dictionary.get("keywords"), packages = dictionary.get("packages"), tex = dictionary.get("tex"), title = dictionary.get("title")
							).items():
								with open(join(targetDirectoryPath, key), "w", encoding = encoding, newline = "") as f:
									f.write(newline.join(value) if isinstance(value, (tuple, list)) else str(value))
							
							# Copy #
							if "figures" in dictionary:
								figureDictionary = []
								if isinstance(dictionary["figures"], (tuple, list)):
									for figure in dictionary["figures"]:
										if isinstance(figure, dict) and "type" in figure and isinstance(figure["type"], str):
											figureDictionary.append(figure)
								elif isinstance(dictionary["figures"], dict) and "type" in dictionary["figures"] and isinstance(dictionary["figures"]["type"], str):
									figureDictionary.append(dictionary["figures"])
								for figure in figureDictionary:
									if figure["type"] == "base64":
										if (
											"base64" in figure and isinstance(figure["base64"], str) and "name" in figure
											and sep not in figure["name"] and "/" not in figure["name"]
										):
											base64String = "".join(character for character in figure["base64"] if (
												character in "+,-;=_" or '/' <= character <= '9' or 'A' <= character <= 'Z' or 'a' <= character <= 'z'
											))
											base64String = base64String.split(";base64,")[-1] if ";base64," in base64String else base64String
											with open(join(targetDirectoryPath, figure["name"]), "wb") as f:
												f.write((urlsafe_b64decode if '-' in base64String or '_' in base64String else b64decode)(base64String))
									elif figure["type"] == "directory":
										if "path" in figure and isinstance(figure["path"], str):
											copytree(figure["path"], targetDirectoryPath, dirs_exist_ok = True)
									elif figure["type"] == "file":
										if "path" in figure and isinstance(figure["path"], str):
											copy(figure["path"], join(targetDirectoryPath, ""))
							
							# Compile #
							engine = Builder.__DefaultEngine
							if "engine" in target["template"]:
								engine = target["template"]["engine"]
								if engine not in Builder.__Engines:
									engine = Builder.__DefaultEngine
							result = run(
								(engine, targetFileName), capture_output = True, text = True, 
								timeout = Builder.__DefaultCompilationTimeout, cwd = targetDirectoryPath
							)
							if EXIT_SUCCESS == result.returncode:
								diagnostics["succeeded"].append(identifier)
							else:
								diagnostics["failed"][identifier] = result
						except TimeoutExpired as innerBaseException:
							diagnostics["failed"][identifier] = {
								"cmd":innerBaseException.cmd, "stderr":innerBaseException.stderr, 
								"stdout":innerBaseException.stdout, "timeout":innerBaseException.timeout
							}
						#except BaseException as innerBaseException:#########
						#	diagnostics["failed"][identifier] = innerBaseException
				else:
					diagnostics["mismatched"] += 1
		except KeyError as outerBaseException:#####
			diagnostics["aborted"] = outerBaseException
		return diagnostics

class Builders:
	def __init__(self:object) -> object:
		self.__filePaths = []
		self.__builders = []
	def updateFilePaths(self:object, *paths:tuple) -> int:
		originalLength, stack = len(self.__builders), list(reversed(paths))
		while stack:
			element = stack.pop()
			if isinstance(element, (tuple, list)):
				stack.extend(reversed(element))
			elif isinstance(element, set):
				stack.extend(sorted(element, reverse = True))
			elif isinstance(element, str):
				if not islink(element):
					if isdir(element):
						filePaths = []
						for root, directoryNames, fileNames in walk(element):
							for fileName in fileNames:
								relativeFilePath = relpath(join(root, fileName))
								if (
									not islink(relativeFilePath) and isfile(relativeFilePath)
									and splitext(fileName)[1].lower() == ".json"
									and relativeFilePath not in self.__filePaths
								):
									filePaths.append(relativeFilePath)
						filePaths.sort()
						self.__filePaths.extend(filePaths)
						del filePaths
					elif isfile(element):
						fileName = basename(element)
						if splitext(fileName)[1] == ".json":
							relativeFilePath = relpath(element)
							if relativeFilePath not in self.__filePaths:
								self.__filePaths.append(relativeFilePath)
		for filePath in self.__filePaths[originalLength:]:
			self.__builders.append(Builder(filePath))
		currentLength = len(self.__builders)
		return currentLength - originalLength
	def build(self:object) -> int:
		successCount = 0
		for filePath, builder in zip(self.__filePaths, self.__builders):
			diagnostics = builder.build()
			if diagnostics["aborted"] is None:
				if diagnostics["failed"] or diagnostics["mismatched"]:
					print("Built {0} with {1} succeeded, {2} failed, and {3} template(s) mismatched. ".format(
						repr(filePath), diagnostics["succeeded"], diagnostics["failed"], diagnostics["mismatched"]
					))
				else:
					successCount += 1
					print("Successfully built {0} with {1} succeeded. ".format(repr(filePath), diagnostics["succeeded"]))
			else:
				print("Failed to build {0} due to {1}. ".format(repr(filePath), repr(diagnostics["aborted"])))
		return successCount


def main() -> int:
	builders = Builders()
	totalCount = builders.updateFilePaths(argv[1:])
	if totalCount >= 1:
		successCount = builders.build()
		errorLevel = EXIT_SUCCESS if successCount == totalCount else EXIT_FAILURE
	else:
		errorLevel = EOF
	return errorLevel



if "__main__" == __name__:
	exit(main())