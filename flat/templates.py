from os import linesep, listdir
from os.path import isabs, isdir, isfile, islink, join, splitext
from re import PatternError, compile
DEFAULT_ENCODING = "utf-8"
STRIPPED_CHARACTERS = "\t\n\r"
DEFAULT_PATTERN = "^.+$"


class File:
	@staticmethod
	def read(filePath:str, encoding:str = DEFAULT_ENCODING) -> list:
		if isinstance(filePath, str):
			with open(filePath, "r", encoding = encoding) as f: # the exceptions should be handled in the upper level of templates
				return f.read().strip(STRIPPED_CHARACTERS).splitlines()
		else:
			return []

class Directory:
	@staticmethod
	def read(directoryPath:str, filter:str = DEFAULT_PATTERN, reverse:bool = False, doubleLineSeparators:bool = True, encoding:str = DEFAULT_ENCODING) -> list:
		if isinstance(directoryPath, str):
			try:
				pattern = compile(filter)
			except PatternError:
				pattern = compile(DEFAULT_PATTERN)
			filePaths = []
			for entryName in listdir(directoryPath):
				entryPath = join(directoryPath, entryName)
				if not islink(entryPath) and isfile(entryPath) and pattern.search(entryName):
					filePaths.append(entryPath)
			filePaths.sort(reverse = reverse is True)
			stringBuffer = []
			for filePath in filePaths:
				stringBuffer.extend(File.read(filePath, encoding = encoding))
				if doubleLineSeparators is not False:
					stringBuffer.append("")
			if stringBuffer and not stringBuffer[-1]:
				stringBuffer.pop()
			return stringBuffer
		else:
			return []

class Templates:
	@staticmethod
	def _readSources(baseDirectoryPath:str, sourceDefinitions:object, defaultFilter:str, doubleLineSeparators:bool = True, separateSources:bool = False) -> list:
		sourceDictionary = []
		if isinstance(sourceDefinitions, (tuple, list)):
			for sourceDefinition in sourceDefinitions:
				if isinstance(sourceDefinition, dict) and sourceDefinition.get("type") in ("directory", "file", "text"):
					sourceDictionary.append(sourceDefinition)
		elif isinstance(sourceDefinitions, dict) and sourceDefinitions.get("type") in ("directory", "file", "text"):
			sourceDictionary.append(sourceDefinitions)
		stringBuffer = []
		for sourceDefinition in sourceDictionary:
			if "directory" == sourceDefinition["type"]:
				if "path" in sourceDefinition and isinstance(sourceDefinition["path"], str):
					stringBuffer.extend(Directory.read(
						join(baseDirectoryPath, sourceDefinition["path"]), filter = sourceDefinition.get("filter", defaultFilter),
						reverse = sourceDefinition.get("reverse") is True, doubleLineSeparators = doubleLineSeparators,
						encoding = sourceDefinition.get("encoding", DEFAULT_ENCODING)
					))
			elif "file" == sourceDefinition["type"]:
				if "path" in sourceDefinition and isinstance(sourceDefinition["path"], str):
					stringBuffer.extend(File.read(
						join(baseDirectoryPath, sourceDefinition["path"]), encoding = sourceDefinition.get("encoding", DEFAULT_ENCODING)
					))
			elif "text" == sourceDefinition["type"]:
				if "text" in sourceDefinition and isinstance(sourceDefinition["text"], str):
					stringBuffer.append(sourceDefinition["text"].strip())
			if separateSources is True:
				stringBuffer.append("")
		return stringBuffer

	@staticmethod
	def _collectAuthors(authorDefinitions:object) -> tuple:
		authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = [], [], {}, [], []
		if isinstance(authorDefinitions, (tuple, list)):
			for author in authorDefinitions:
				if isinstance(author, dict):
					authors.append(author)
		for authorIndex, author in enumerate(authors):
			authorAffiliations = []
			if "affiliations" in author:
				if isinstance(author["affiliations"], (tuple, list)):
					for affiliation in author["affiliations"]:
						if isinstance(affiliation, str):
							authorAffiliations.append(affiliation)
				elif isinstance(author["affiliations"], str):
					authorAffiliations.append(author["affiliations"])
			for affiliation in authorAffiliations:
				try:
					authorAffiliationIndex = str(affiliations.index(affiliation) + 1)
				except ValueError:
					affiliations.append(affiliation)
					authorAffiliationIndex = str(len(affiliations))
				authorAffiliationIndexSequences.setdefault(authorIndex, [])
				authorAffiliationIndexSequences[authorIndex].append(authorAffiliationIndex)
			if author.get("FA") is True:
				coFirstAuthorIndexes.append(authorIndex)
			if author.get("CA") is True:
				coCorrespondingAuthorIndexes.append(authorIndex)
		if len(coFirstAuthorIndexes) < 2:
			coFirstAuthorIndexes.clear()
		return authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes

	@staticmethod
	def _getEmails(author:dict) -> list:
		emails = []
		if isinstance(author, dict) and "email" in author:
			if isinstance(author["email"], str):
				emails.append(author["email"])
			elif isinstance(author["email"], (tuple, list)):
				for email in author["email"]:
					if isinstance(email, str):
						emails.append(email)
		return emails

	@staticmethod
	def _getAuthorCitation(author:dict) -> str:
		name = author["name"].strip() if isinstance(author, dict) and "name" in author and isinstance(author["name"], str) else ""
		nameParts = name.split()
		if len(nameParts) >= 2:
			return "{0} {1}".format(nameParts[-1], "".join(namePart[0] for namePart in nameParts[:-1] if namePart))
		else:
			return name

	@staticmethod
	def _joinAuthors(authorStrings:list) -> str:
		if len(authorStrings) >= 3:
			return "{0}, and {1}".format(", ".join(authorStrings[:-1]), authorStrings[-1])
		elif len(authorStrings) == 2:
			return "{0} and {1}".format(authorStrings[0], authorStrings[1])
		elif len(authorStrings) == 1:
			return authorStrings[0]
		else:
			return ""

	@staticmethod
	def _getOrdinal(number:int) -> str:
		remainder = number % 100
		if 11 <= remainder <= 13:
			suffix = "th"
		else:
			suffix = {1:"st", 2:"nd", 3:"rd"}.get(number % 10, "th")
		return "{0}\\textsuperscript{{{1}}}".format(number, suffix)

	class ACM:
		KeywordSeparator = ", "
		class Conferences:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[sigconf]{acmart}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						if isinstance(package, str) and not any(
							excludedPackage in package for excludedPackage in ("amsmath", "amssymb", "amsfonts", "natbib")
						):
							stringBuffer.append(package)
				stringBuffer.extend([
					"\\newcommand{\\keywordSeparator}{, }", "",
					"\\AtBeginDocument{%",
					"\t\\providecommand\\BibTeX{%",
					"\t\t{%",
					"\t\t\tBib\\TeX",
					"\t\t}",
					"\t}",
					"}",
					"\\setcopyright{acmlicensed}",
					"\\copyrightyear{2018}",
					"\\acmYear{2018}",
					"\\acmDOI{XXXXXXX.XXXXXXX}",
					"\\acmConference[Conference acronym 'XX]{Make sure to enter the correct conference title from your rights confirmation email}{June 03--05, 2018}{Woodstock, NY}",
					"\\acmISBN{978-1-4503-XXXX-X/18/06}", "",
					"\\begin{document}", ""
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				for authorIndex, author in enumerate(authors):
					authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
					if authorIndex in coFirstAuthorIndexes:
						authorName += "\\textsuperscript{\\#}"
					if authorIndex in coCorrespondingAuthorIndexes:
						authorName += "*"
					stringBuffer.append("\\author{{{0}}}".format(authorName))
					if authorIndex in authorAffiliationIndexSequences:
						for affiliationIndex in authorAffiliationIndexSequences[authorIndex]:
							stringBuffer.extend([
								"\\affiliation{%",
								"\t\\institution{{{0}}}".format(affiliations[int(affiliationIndex) - 1]),
								"\t\\country{}",
								"}"
							])
					emails = Templates._getEmails(author)
					if emails:
						stringBuffer.append("\\email{{{0}}}".format(", ".join(emails)))
					if "ORCID" in author and isinstance(author["ORCID"], str):
						stringBuffer.append("\\orcid{{{0}}}".format(author["ORCID"]))
					stringBuffer.append("")
				if authors:
					shortAuthors = kwargs["shortAuthors"] if "shortAuthors" in kwargs and isinstance(kwargs["shortAuthors"], str) else ", ".join(
						Templates._getAuthorCitation(author) for author in authors[:3]
					) + (", et al. " if len(authors) >= 4 else "")
					stringBuffer.append("\\renewcommand{{\\shortauthors}}{{{0}}}".format(shortAuthors))
					stringBuffer.append("")

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\begin{abstract}")
					for abstract in abstractBuffer:
						stringBuffer.append("\t" + abstract)
					stringBuffer.append("\\end{abstract}")
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\keywords{{{0}}}".format(Templates.ACM.KeywordSeparator.join(kwargs["keywords"])))
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\keywords{{{0}}}".format(kwargs["keywords"]))
						stringBuffer.append("")
				stringBuffer.extend([
					"\\received{3 November 2024}",
					"\\received[revised]{26 November 2024}",
					"\\received[accepted]{10 February 2025}", "",
					"\\maketitle", ""
				])
				if coCorrespondingAuthorIndexes:
					stringBuffer.extend([
						"\\renewcommand{\\thefootnote}{}",
						"\\footnotetext{{* {0} }}".format(
							"These are the corresponding authors." if len(coCorrespondingAuthorIndexes) >= 2 else "This is the corresponding author."
						), ""
					])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\bibliographystyle{ACM-Reference-Format}",
						"\\bibliography{ref.bib}", ""
					])
				stringBuffer.extend(["\\end{document}", "\\endinput"])
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class Elsevier:
		KeywordSeparator = "\\sep"
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[a4paper,fleqn]{cas-dc}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						stringBuffer.append(package)
				stringBuffer.append("")
				stringBuffer.append("\\begin{document}")
				stringBuffer.append("")
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title[mode=title]{{{0}}}".format(title))
				shortTitle = kwargs["shortTitle"] if "shortTitle" in kwargs and isinstance(kwargs["shortTitle"], str) else title
				stringBuffer.append("\\shorttitle{{{0}}}".format(shortTitle))
				stringBuffer.append("")
				
				# Authors and affiliations #
				if "authors" in kwargs and isinstance(kwargs["authors"], (tuple, list)):
					# Collect affiliations #
					affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = [], {}, [], []
					for authorIndex, author in enumerate(kwargs["authors"]):
						if isinstance(author, dict) and "affiliations" in author:
							authorAffiliations = []
							if isinstance(author["affiliations"], (tuple, list)):
								for affiliation in author["affiliations"]:
									if isinstance(affiliation, str):
										authorAffiliations.append(affiliation)
							elif isinstance(kwargs["authors"]["affiliations"], str):
								authorAffiliations.append(kwargs["authors"]["affiliations"])
							for affiliation in authorAffiliations:
								try: # to avoid search twice
									authorAffiliationIndex = str(affiliations.index(affiliation) + 1)
									authorAffiliationIndexSequences.setdefault(authorIndex, [])
									authorAffiliationIndexSequences[authorIndex].append(authorAffiliationIndex)
								except ValueError:
									authorAffiliationIndex = str(len(affiliations) + 1)
									affiliations.append(affiliation)
									authorAffiliationIndexSequences.setdefault(authorIndex, [])
									authorAffiliationIndexSequences[authorIndex].append(authorAffiliationIndex)
							if "FA" in author and author["FA"] is True:
								coFirstAuthorIndexes.append(authorIndex)
							if "CA" in author and author["CA"] is True:
								coCorrespondingAuthorIndexes.append(authorIndex)
					if len(coFirstAuthorIndexes) < 2: # disable co-first author marks if there are fewer than 2 co-first authors
						coFirstAuthorIndexes.clear()
					
					# Generate authors and affiliations #
					for authorIndex, author in enumerate(kwargs["authors"]):
						if isinstance(author, dict):
							stringBuffer.append("\\author{0}{{{1}}}{2}{3}{4}".format(
								"[{0}]".format(",".join(authorAffiliationIndexSequences[authorIndex])) if authorIndex in authorAffiliationIndexSequences else "", 
								author["name"] if "name" in author and isinstance(author["name"], str) else "", 
								"[orcid={0}]".format(author["ORCID"]) if "ORCID" in author and isinstance(author["ORCID"], str) else "", 
								"\\fnmark[1]" if authorIndex in coFirstAuthorIndexes else "", 
								"\\cormark[1]" if authorIndex in coCorrespondingAuthorIndexes else ""
							))
							if "email" in author:
								if isinstance(author["email"], str):
									stringBuffer.append("\\ead{{{0}}}".format(author["email"]))
								elif isinstance(author["email"], (tuple, list)) and author["email"] and isinstance(author["email"], str):
									stringBuffer.append("\\ead{{{0}}}".format(author["email"][0]))
							stringBuffer.append("")
					for affiliationIndex, affiliation in enumerate(affiliations):
						stringBuffer.append("\\address[{0}]{{{1}}}".format(affiliationIndex + 1, affiliation))
					stringBuffer.append("")
					if len(coCorrespondingAuthorIndexes) >= 2:
						stringBuffer.append("\\nonumnote{* These are the corresponding authors. }")
						if len(coFirstAuthorIndexes) < 2:
							stringBuffer.append("")
					elif len(coCorrespondingAuthorIndexes) == 1:
						stringBuffer.append("\\nonumnote{* This is the corresponding author. }")
						if len(coFirstAuthorIndexes) < 2:
							stringBuffer.append("")
					if len(coFirstAuthorIndexes) >= 2:
						stringBuffer.append("\\fntext[1]{Co-first authors contributed equally to this work. }")
						stringBuffer.append("")
				
				# Abstract #
				if "abstract" in kwargs:
					abstractDictionary = []
					if isinstance(kwargs["abstract"], (tuple, list)):
						for abstract in kwargs["abstract"]:
							if isinstance(abstract, dict) and abstract.get("type") in ("directory", "file", "text"):
								abstractDictionary.append(abstract)
					elif isinstance(kwargs["abstract"], dict) and kwargs["abstract"].get("type") in ("directory", "file", "text"):
						abstractDictionary.append(kwargs["abstract"])
					abstractBuffer = []
					for abstract in abstractDictionary:
						if "directory" == abstract["type"]:
							if "path" in abstract and isinstance(abstract["path"], str):
								abstractBuffer.extend(Directory.read(
									join(baseDirectoryPath, abstract["path"]), filter = abstract.get("filter", "^.*\\.tex$"), reverse = abstract.get("reverse") is True, 
									doubleLineSeparators = False, encoding = abstract.get("encoding", DEFAULT_ENCODING)
								))
						elif "file" == abstract["type"]:
							if "path" in abstract and isinstance(abstract["path"], str):
								abstractBuffer.extend(File.read(join(baseDirectoryPath, abstract["path"]), encoding = abstract.get("encoding", DEFAULT_ENCODING)))
						elif "text" == abstract["type"]:
							if "text" in abstract and isinstance(abstract["text"], str):
								abstractBuffer.append(abstract["text"].strip())
					if abstractBuffer:
						stringBuffer.append("\\begin{abstract}")
						for abstract in abstractBuffer:
							stringBuffer.append("\t" + abstract)
						stringBuffer.append("\\end{abstract}")
						stringBuffer.append("")
						abstractBuffer.clear()
						del abstractBuffer
				
				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\begin{keywords}")
						stringBuffer.append("\t" + "\\sep{}".join(kwargs["keywords"]))
						stringBuffer.append("\\end{keywords}")
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\begin{keywords}")
						stringBuffer.append("\t{0}".format(kwargs["keywords"]))
						stringBuffer.append("\\end{keywords}")
						stringBuffer.append("")
				stringBuffer.append("\\maketitle")
				stringBuffer.append("")
				
				# TeX #
				if "tex" in kwargs:
					texDictionary = []
					if isinstance(kwargs["tex"], (tuple, list)):
						for tex in kwargs["tex"]:
							if isinstance(tex, dict) and tex.get("type") in ("directory", "file", "text"):
								texDictionary.append(tex)
					elif isinstance(kwargs["tex"], dict) and kwargs["tex"].get("type") in ("directory", "file", "text"):
						texDictionary.append(kwargs["tex"])
					for tex in texDictionary:
						if "directory" == tex["type"]:
							if "path" in tex and isinstance(tex["path"], str):
								stringBuffer.extend(Directory.read(
									join(baseDirectoryPath, tex["path"]), filter = tex.get("filter", "^.*\\.tex$"), 
									reverse = tex.get("reverse") is True, encoding = tex.get("encoding", DEFAULT_ENCODING)
								))
						elif "file" == tex["type"]:
							if "path" in tex and isinstance(tex["path"], str):
								stringBuffer.extend(File.read(join(baseDirectoryPath, tex["path"]), encoding = tex.get("encoding", DEFAULT_ENCODING)))
						elif "text" == tex["type"]:
							if "text" in tex and isinstance(tex["text"], str):
								stringBuffer.append(tex["text"].strip())
						stringBuffer.append("")
				stringBuffer.append("\\printcredits{}")
				stringBuffer.append("")
				
				# Bib #
				dictionary = {}
				if "bib" in kwargs:
					bibDictionary = []
					if isinstance(kwargs["bib"], (tuple, list)):
						for bib in kwargs["bib"]:
							if isinstance(bib, dict) and bib.get("type") in ("directory", "file", "bibt"):
								bibDictionary.append(bib)
					elif isinstance(kwargs["bib"], dict) and kwargs["bib"].get("type") in ("directory", "file", "bibt"):
						bibDictionary.append(kwargs["bib"])
					bibBuffer = []
					for bib in bibDictionary:
						if "directory" == bib["type"]:
							if "path" in bib and isinstance(bib["path"], str):
								bibBuffer.extend(Directory.read(
									join(baseDirectoryPath, bib["path"]), filter = bib.get("filter", "^.*\\.bib$"), 
									reverse = bib.get("reverse") is True, encoding = bib.get("encoding", DEFAULT_ENCODING)
								))
						elif "file" == bib["type"]:
							if "path" in bib and isinstance(bib["path"], str):
								bibBuffer.extend(File.read(join(baseDirectoryPath, bib["path"]), encoding = bib.get("encoding", DEFAULT_ENCODING)))
						elif "text" == bib["type"]:
							if "text" in bib and isinstance(bib["text"], str):
								bibBuffer.append(bib["text"].strip())
						bibBuffer.append("")
					if bibBuffer:
						dictionary["ref.bib"] = bibBuffer
						stringBuffer.append("\\bibliographystyle{unsrt}")
						stringBuffer.append("\\bibliography{{{0}}}".format("ref.bib"))
						stringBuffer.append("")
				
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class IEEE:
		KeywordSeparator = "; "
		class Conferences:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[conference,compsoc]{IEEEtran}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						stringBuffer.append(package)
				stringBuffer.extend([
					"\\newcommand{\\keywordSeparator}{; }", "",
					"\\makeatletter",
					"\\newcommand{\\linebreakand}{%",
					"\t\\end{@IEEEauthorhalign}",
					"\t\\hfill\\mbox{}\\par",
					"\t\\mbox{}\\hfill\\begin{@IEEEauthorhalign}",
					"}",
					"\\makeatother", "",
					"\\begin{document}", ""
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				if authors:
					correspondingAuthorStrings = []
					for authorIndex in coCorrespondingAuthorIndexes:
						author = authors[authorIndex]
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						emails = Templates._getEmails(author)
						correspondingAuthorStrings.append(
							"{0} ({1})".format(authorName, ", ".join(emails)) if emails else authorName
						)
					stringBuffer.append("\\author{")
					nonCoFirstAuthorRank = 2
					for authorIndex, author in enumerate(authors):
						if authorIndex >= 1:
							stringBuffer.append("\t\\linebreakand" if authorIndex % 2 == 0 else "\t\\and")
						authorRank = 1 if authorIndex in coFirstAuthorIndexes else (
							nonCoFirstAuthorRank if coFirstAuthorIndexes else authorIndex + 1
						)
						if coFirstAuthorIndexes and authorIndex not in coFirstAuthorIndexes:
							nonCoFirstAuthorRank += 1
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						if authorIndex in coCorrespondingAuthorIndexes:
							authorName += "*"
						if coCorrespondingAuthorIndexes and authorIndex == coCorrespondingAuthorIndexes[-1]:
							authorName += "\\thanks{{* {0} }}".format(
								"Corresponding authors: {0}.".format(Templates._joinAuthors(correspondingAuthorStrings))
								if len(coCorrespondingAuthorIndexes) >= 2 else "Corresponding author: {0}.".format(correspondingAuthorStrings[0])
							)
						stringBuffer.append("\t\\IEEEauthorblockN{{{0} {1}}}".format(Templates._getOrdinal(authorRank), authorName))
						stringBuffer.append("\t\\IEEEauthorblockA{")
						if authorIndex in authorAffiliationIndexSequences:
							for affiliationIndex in authorAffiliationIndexSequences[authorIndex]:
								stringBuffer.append("\t\t\\textit{{{0}}} \\\\".format(affiliations[int(affiliationIndex) - 1]))
						emails = Templates._getEmails(author)
						if emails:
							stringBuffer.append("\t\t\\url{{{0}}}".format(", ".join(emails)))
						stringBuffer.append("\t}")
					stringBuffer.append("}")
					stringBuffer.append("")
				stringBuffer.extend(["\\maketitle", ""])

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\begin{abstract}")
					for abstract in abstractBuffer:
						stringBuffer.append("\t" + abstract)
					stringBuffer.append("\\end{abstract}")
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.extend([
							"\\begin{IEEEkeywords}",
							"\t" + Templates.IEEE.KeywordSeparator.join(kwargs["keywords"]),
							"\\end{IEEEkeywords}", ""
						])
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.extend([
							"\\begin{IEEEkeywords}",
							"\t" + kwargs["keywords"],
							"\\end{IEEEkeywords}", ""
						])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\bibliographystyle{IEEEtran}",
						"\\bibliography{ref.bib}", ""
					])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
		class Journals:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[lettersize,journal]{IEEEtran}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						stringBuffer.append(package)
				stringBuffer.extend([
					"\\newcommand{\\keywordSeparator}{; }", "",
					"\\begin{document}", ""
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				if authors:
					authorStrings = []
					for authorIndex, author in enumerate(authors):
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						if authorIndex in coFirstAuthorIndexes:
							authorName += "\\textsuperscript{\\#}"
						if authorIndex in coCorrespondingAuthorIndexes:
							authorName += "*"
						if authorIndex in authorAffiliationIndexSequences:
							authorAffiliations = [
								affiliations[int(affiliationIndex) - 1] for affiliationIndex in authorAffiliationIndexSequences[authorIndex]
							]
							if len(authorAffiliations) >= 2:
								affiliationDescription = "{0}; and {1}".format("; ".join(authorAffiliations[:-1]), authorAffiliations[-1])
							elif authorAffiliations:
								affiliationDescription = authorAffiliations[0]
							else:
								affiliationDescription = ""
							authorName += "\\thanks{{{0} was with {1}. }}".format(
								author["name"] if "name" in author and isinstance(author["name"], str) else "", affiliationDescription
							)
						authorStrings.append(authorName)
					stringBuffer.append("\\author{")
					for authorIndex, authorString in enumerate(authorStrings):
						if authorIndex == len(authorStrings) - 1 and len(authorStrings) >= 2:
							prefix = "\tand "
						else:
							prefix = "\t"
						stringBuffer.append(prefix + authorString + (", " if authorIndex < len(authorStrings) - 1 else ""))
					if coFirstAuthorIndexes:
						coFirstAuthorNames = [
							authors[authorIndex].get("name", "") for authorIndex in coFirstAuthorIndexes
						]
						stringBuffer.append("\t\\thanks{{\\textsuperscript{{\\#}}{0} are the co-first authors who contributed equally to this work. }}".format(
							Templates._joinAuthors(coFirstAuthorNames)
						))
					if coCorrespondingAuthorIndexes:
						correspondingAuthorStrings = []
						for authorIndex in coCorrespondingAuthorIndexes:
							author = authors[authorIndex]
							authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
							emails = Templates._getEmails(author)
							correspondingAuthorStrings.append(
								"{0} ({1})".format(authorName, "\\protect\\url{{{0}}}".format(", ".join(emails))) if emails else authorName
							)
						stringBuffer.append("\t\\thanks{{*{0} {1}. }}".format(
							Templates._joinAuthors(correspondingAuthorStrings),
							"are the corresponding authors" if len(coCorrespondingAuthorIndexes) >= 2 else "is the corresponding author"
						))
					stringBuffer.append("}")
					stringBuffer.append("")
				stringBuffer.extend(["\\maketitle", ""])

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\begin{abstract}")
					for abstract in abstractBuffer:
						stringBuffer.append("\t" + abstract)
					stringBuffer.append("\\end{abstract}")
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.extend([
							"\\begin{IEEEkeywords}",
							"\t" + Templates.IEEE.KeywordSeparator.join(kwargs["keywords"]),
							"\\end{IEEEkeywords}", ""
						])
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.extend([
							"\\begin{IEEEkeywords}",
							"\t" + kwargs["keywords"],
							"\\end{IEEEkeywords}", ""
						])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\bibliographystyle{IEEEtran}",
						"\\bibliography{ref.bib}", ""
					])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class MDPI:
		KeywordSeparator = "; "
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = [
					"\\documentclass[journal,article,submit,pdftex,moreauthors]{Definitions/mdpi}",
					"\\firstpage{1}",
					"\\makeatletter",
					"\\setcounter{page}{\\@firstpage}",
					"\\makeatother",
					"\\pubvolume{1}",
					"\\issuenum{1}",
					"\\articlenumber{0}",
					"\\pubyear{2025}",
					"\\copyrightyear{2025}",
					"\\datereceived{ }",
					"\\daterevised{ }",
					"\\dateaccepted{ }",
					"\\datepublished{ }",
					"\\hreflink{https://doi.org/}", ""
				]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						if isinstance(package, str) and not any(
							excludedPackage in package for excludedPackage in ("xcolor", "natbib")
						):
							stringBuffer.append(package)
				stringBuffer.extend(["\\newcommand{\\keywordSeparator}{; }", ""])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\Title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				if authors:
					authorCitations = [Templates._getAuthorCitation(author) for author in authors]
					shortAuthorCitation = ", ".join(authorCitations[:3]) + (", et al" if len(authorCitations) >= 4 else "")
					stringBuffer.extend([
						"\\AuthorCitation{{{0}}}".format(shortAuthorCitation),
						"\\TitleCitation{{{0}}}".format(title), ""
					])
					for authorIndex, author in enumerate(authors):
						if authorIndex < 26 and "ORCID" in author and isinstance(author["ORCID"], str):
							stringBuffer.append("\\newcommand{{\\orcidauthor{0}}}{{{1}}}".format(
								chr(65 + authorIndex), author["ORCID"]
							))
					stringBuffer.append("")
					authorStrings = []
					for authorIndex, author in enumerate(authors):
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						authorMarks = list(authorAffiliationIndexSequences.get(authorIndex, []))
						if authorIndex in coFirstAuthorIndexes:
							authorMarks.append("\\#")
						if authorIndex in coCorrespondingAuthorIndexes:
							authorMarks.append("*")
						if authorMarks:
							authorName += "$^{{{0}}}$".format(",".join(authorMarks))
						if authorIndex < 26 and "ORCID" in author and isinstance(author["ORCID"], str):
							authorName += "\\orcid{0}{{}}".format(chr(65 + authorIndex))
						authorStrings.append(authorName)
					stringBuffer.append("\\Author{{{0}}}".format(Templates._joinAuthors(authorStrings)))
					stringBuffer.append("")
					stringBuffer.append("\\AuthorNames{{{0}}}".format(", ".join(
						author["name"] if "name" in author and isinstance(author["name"], str) else "" for author in authors
					)))
					stringBuffer.append("")
					if affiliations:
						stringBuffer.append("\\address{%")
						for affiliationIndex, affiliation in enumerate(affiliations):
							lineSuffix = ";\\\\" if affiliationIndex < len(affiliations) - 1 else ";"
							stringBuffer.append("\t$^{{{0}}}$ \\quad {1}{2}".format(affiliationIndex + 1, affiliation, lineSuffix))
						stringBuffer.append("}")
						stringBuffer.append("")
					if coCorrespondingAuthorIndexes:
						correspondingAuthorEmails = []
						for authorIndex in coCorrespondingAuthorIndexes:
							correspondingAuthorEmails.extend(Templates._getEmails(authors[authorIndex]))
						stringBuffer.append("\\corres{{Correspondence: {0}{1}}}".format(
							"; ".join(correspondingAuthorEmails), ";" if correspondingAuthorEmails else ""
						))
						stringBuffer.append("")
					if coFirstAuthorIndexes:
						stringBuffer.append("\\firstnote{These authors contributed equally to this work. }")
						stringBuffer.append("")

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\abstract{{{0}}}".format(" ".join(abstractBuffer)))
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\keyword{{{0}}}".format(Templates.MDPI.KeywordSeparator.join(kwargs["keywords"])))
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\keyword{{{0}}}".format(kwargs["keywords"]))
						stringBuffer.append("")
				stringBuffer.extend(["\\begin{document}", ""])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\begin{adjustwidth}{-\\extralength}{0cm}",
						"\\reftitle{References}",
						"\\bibliography{ref.bib}",
						"\\PublishersNote{}",
						"\\end{adjustwidth}", ""
					])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class Nature:
		KeywordSeparator = ", "
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[fleqn,10pt]{wlscirep}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						stringBuffer.append(package)
				stringBuffer.extend([
					"\\usepackage[utf8]{inputenc}",
					"\\usepackage[T1]{fontenc}"
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				for authorIndex, author in enumerate(authors):
					authorMarks = list(authorAffiliationIndexSequences.get(authorIndex, []))
					if authorIndex in coFirstAuthorIndexes:
						authorMarks.append("+")
					if authorIndex in coCorrespondingAuthorIndexes:
						authorMarks.append("*")
					authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
					stringBuffer.append("\\author{0}{{{1}}}".format(
						"[{0}]".format(",".join(authorMarks)) if authorMarks else "", authorName
					))
				for affiliationIndex, affiliation in enumerate(affiliations):
					stringBuffer.append("\\affil[{0}]{{{1}}}".format(affiliationIndex + 1, affiliation))
				if coFirstAuthorIndexes:
					stringBuffer.append("\\affil[+]{These authors contributed equally to this work. }")
				if coCorrespondingAuthorIndexes:
					correspondingAuthorStrings = []
					for authorIndex in coCorrespondingAuthorIndexes:
						author = authors[authorIndex]
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						emails = Templates._getEmails(author)
						correspondingAuthorStrings.append(
							"{0} ({1})".format(authorName, ", ".join(emails)) if emails else authorName
						)
					stringBuffer.append("\\affil[*]{{Corresponding {0}: {1}}}".format(
						"authors" if len(coCorrespondingAuthorIndexes) >= 2 else "author",
						Templates._joinAuthors(correspondingAuthorStrings)
					))
				if authors or affiliations:
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\keywords{{{0}}}".format(Templates.Nature.KeywordSeparator.join(kwargs["keywords"])))
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\keywords{{{0}}}".format(kwargs["keywords"]))
						stringBuffer.append("")

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\begin{abstract}")
					for abstract in abstractBuffer:
						stringBuffer.append("\t" + abstract)
					stringBuffer.append("\\end{abstract}")
					stringBuffer.append("")
				stringBuffer.extend([
					"\\begin{document}", "",
					"\\flushbottom",
					"\\maketitle", ""
				])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend(["\\bibliography{ref.bib}", ""])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class Springer:
		KeywordSeparator = " \\and "
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[runningheads]{llncs}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						stringBuffer.append(package)
				stringBuffer.extend([
					"\\newcommand{\\keywordSeparator}{ \\and}", "",
					"\\begin{document}", ""
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				if authors:
					stringBuffer.append("\\author{")
					for authorIndex, author in enumerate(authors):
						authorMarks = list(authorAffiliationIndexSequences.get(authorIndex, []))
						if authorIndex in coFirstAuthorIndexes:
							authorMarks.append("\\#")
						if authorIndex in coCorrespondingAuthorIndexes:
							authorMarks.append("*")
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						stringBuffer.append("\t{0}{1}{2}".format(
							"\\and " if authorIndex >= 1 else "", authorName,
							"\\inst{{{0}}}".format(",".join(authorMarks)) if authorMarks else ""
						))
					stringBuffer.append("}")
					stringBuffer.append("")
					shortAuthors = kwargs["shortAuthors"] if "shortAuthors" in kwargs and isinstance(kwargs["shortAuthors"], str) else (
						"{0} et al. ".format(Templates._getAuthorCitation(authors[0])) if len(authors) >= 2 else Templates._getAuthorCitation(authors[0])
					)
					stringBuffer.append("\\authorrunning{{{0}}}".format(shortAuthors))
					stringBuffer.append("")
				if affiliations:
					stringBuffer.append("\\institute{")
					for affiliationIndex, affiliation in enumerate(affiliations):
						stringBuffer.append("\t{0}{1}".format("\\and " if affiliationIndex >= 1 else "", affiliation))
					stringBuffer.append("}")
					stringBuffer.append("")
				stringBuffer.extend(["\\maketitle", ""])
				if coFirstAuthorIndexes or coCorrespondingAuthorIndexes:
					stringBuffer.append("\\renewcommand{\\thefootnote}{}")
					if coFirstAuthorIndexes:
						stringBuffer.append("\\footnotetext{\\textsuperscript{\\#} Co-first authors contributed equally to this work. }")
					if coCorrespondingAuthorIndexes:
						correspondingAuthorStrings = []
						for authorIndex in coCorrespondingAuthorIndexes:
							author = authors[authorIndex]
							authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
							emails = Templates._getEmails(author)
							correspondingAuthorStrings.append(
								"{0} ({1})".format(authorName, "\\url{{{0}}}".format(", ".join(emails))) if emails else authorName
							)
						stringBuffer.append("\\footnotetext{{* Corresponding author{0}: {1}. }}".format(
							"s" if len(coCorrespondingAuthorIndexes) >= 2 else "", Templates._joinAuthors(correspondingAuthorStrings)
						))
					stringBuffer.append("")

				# Abstract and keywords #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer or kwargs.get("keywords"):
					stringBuffer.append("\\begin{abstract}")
					for abstract in abstractBuffer:
						stringBuffer.append("\t" + abstract)
					if isinstance(kwargs.get("keywords"), (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\t\\keywords{{{0}}}".format(Templates.Springer.KeywordSeparator.join(kwargs["keywords"])))
					elif isinstance(kwargs.get("keywords"), str):
						stringBuffer.append("\t\\keywords{{{0}}}".format(kwargs["keywords"]))
					stringBuffer.append("\\end{abstract}")
					stringBuffer.append("")
				stringBuffer.extend([
					"\\section*{Competing Interests}", "",
					"The authors declare no competing interests.", ""
				])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\bibliographystyle{splncs04}",
						"\\bibliography{ref.bib}", ""
					])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class TSP:
		KeywordSeparator = "; "
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = [
					"\\documentclass[journal,article,submit,moreauthors,pdftex]{Definitions/tsp}",
					"\\input{Definitions/package}",
					"\\include{Definitions/unicode}",
					"\\continuouspages{yes}",
					"\\firstpage{1}",
					"\\makeatletter",
					"\\setcounter{page}{\\@firstpage}",
					"\\makeatother",
					"\\pubvolume{1}",
					"\\issuenum{1}",
					"\\articlenumber{12345}",
					"\\pubyear{2025}",
					"\\copyrightyear{2025}",
					"\\datereceived{Day Month Year}",
					"\\dateaccepted{Day Month Year}",
					"\\dateonlinefirst{}",
					"\\datepublished{}", ""
				]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						if isinstance(package, str) and "natbib" not in package:
							stringBuffer.append(package)
				stringBuffer.extend(["\\newcommand{\\keywordSeparator}{; }", ""])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.append("\\Title{{{0}}}".format(title))
				stringBuffer.append("")

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				if authors:
					for authorIndex, author in enumerate(authors):
						if authorIndex < 26 and "ORCID" in author and isinstance(author["ORCID"], str):
							stringBuffer.append("\\newcommand{{\\orcidauthor{0}}}{{{1}}}".format(
								chr(65 + authorIndex), author["ORCID"]
							))
					stringBuffer.append("")
					authorStrings = []
					for authorIndex, author in enumerate(authors):
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						authorMarks = list(authorAffiliationIndexSequences.get(authorIndex, []))
						if authorIndex in coFirstAuthorIndexes:
							authorMarks.append("\\#")
						if authorIndex in coCorrespondingAuthorIndexes:
							authorMarks.append("*")
						if authorMarks:
							authorName += "\\textsuperscript{{{0}}}".format(",".join(authorMarks))
						if authorIndex < 26 and "ORCID" in author and isinstance(author["ORCID"], str):
							authorName += "\\orcid{0}{{}}".format(chr(65 + authorIndex))
						authorStrings.append(authorName)
					stringBuffer.append("\\Author{")
					for authorIndex, authorString in enumerate(authorStrings):
						stringBuffer.append("\t{0}{1}{2}".format(
							"and " if authorIndex == len(authorStrings) - 1 and len(authorStrings) >= 2 else "",
							authorString,
							"" if authorIndex == len(authorStrings) - 1 else ", "
						))
					stringBuffer.append("}")
					stringBuffer.append("")
					authorCitations = [Templates._getAuthorCitation(author) for author in authors]
					stringBuffer.append("\\AuthorNames{{{0}}}".format(
						", ".join(authorCitations[:3]) + (", et al. " if len(authorCitations) >= 4 else "")
					))
					stringBuffer.append("")
				if affiliations:
					stringBuffer.append("\\address{%")
					for affiliationIndex, affiliation in enumerate(affiliations):
						stringBuffer.append("\t\\textsuperscript{{{0}}} {1}".format(affiliationIndex + 1, affiliation))
						if affiliationIndex < len(affiliations) - 1:
							stringBuffer.append("\t")
					stringBuffer.append("}")
					stringBuffer.append("")
				if coCorrespondingAuthorIndexes:
					correspondingAuthorNames, correspondingAuthorEmails = [], []
					for authorIndex in coCorrespondingAuthorIndexes:
						author = authors[authorIndex]
						correspondingAuthorNames.append(
							author["name"] if "name" in author and isinstance(author["name"], str) else ""
						)
						correspondingAuthorEmails.extend(Templates._getEmails(author))
					stringBuffer.append("\\corres{{Corresponding Author{0}: {1}.{2}}}".format(
						"s" if len(coCorrespondingAuthorIndexes) >= 2 else "",
						Templates._joinAuthors(correspondingAuthorNames),
						" Email: {0}".format(Templates._joinAuthors(correspondingAuthorEmails)) if correspondingAuthorEmails else ""
					))
					stringBuffer.append("")
				if coFirstAuthorIndexes:
					stringBuffer.append("\\firstnote{These authors contributed equally to this work. }")
					stringBuffer.append("\\secondnote{}")
					stringBuffer.append("")

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\abstract{{{0}}}".format(" ".join(abstractBuffer)))
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\keyword{{{0}}}".format(Templates.TSP.KeywordSeparator.join(kwargs["keywords"])))
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\keyword{{{0}}}".format(kwargs["keywords"]))
						stringBuffer.append("")
				stringBuffer.extend(["\\begin{document}", ""])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend([
						"\\reftitle{References}",
						"\\bibliography{ref.bib}", ""
					])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
	class Wiley:
		KeywordSeparator = ", "
		class Publisher:
			@staticmethod
			def format(baseDirectoryPath:str, targetFileName:str, **kwargs:dict) -> dict:
				stringBuffer = ["\\documentclass[AMA,Times1COL]{WileyNJDv5}"]
				if "packages" in kwargs and isinstance(kwargs["packages"], (tuple, list)):
					for package in kwargs["packages"]:
						if isinstance(package, str) and "natbib" not in package:
							stringBuffer.append(package)
				stringBuffer.extend([
					"\\newcommand{\\keywordSeparator}{, }", "",
					"\\articletype{Regular Paper}",
					"\\received{Date Month Year}",
					"\\revised{Date Month Year}",
					"\\accepted{Date Month Year}",
					"\\journal{Journal}",
					"\\volume{00}",
					"\\copyyear{2023}",
					"\\startpage{1}",
					"\\raggedbottom", "",
					"\\begin{document}", ""
				])
				title = kwargs["title"] if "title" in kwargs and isinstance(kwargs["title"], str) else "Title"
				stringBuffer.extend([
					"\\title{{{0}}}".format(title),
					"\\titlemark{{{0}}}".format(title), ""
				])

				# Authors and affiliations #
				authors, affiliations, authorAffiliationIndexSequences, coFirstAuthorIndexes, coCorrespondingAuthorIndexes = Templates._collectAuthors(
					kwargs.get("authors")
				)
				for authorIndex, author in enumerate(authors):
					authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
					stringBuffer.append("\\author{0}{{{1}}}".format(
						"[{0}]".format(",".join(authorAffiliationIndexSequences[authorIndex]))
						if authorIndex in authorAffiliationIndexSequences else "", authorName
					))
				if authors:
					shortAuthors = kwargs["shortAuthors"] if "shortAuthors" in kwargs and isinstance(kwargs["shortAuthors"], str) else (
						", ".join(Templates._getAuthorCitation(author) for author in authors[:3]) + (
							", \\textsc{et al.} " if len(authors) >= 4 else ""
						)
					)
					stringBuffer.append("\\authormark{{{0}}}".format(shortAuthors))
					stringBuffer.append("")
				for affiliationIndex, affiliation in enumerate(affiliations):
					stringBuffer.append("\\address[{0}]{{{1}}}".format(affiliationIndex + 1, affiliation))
				if affiliations:
					stringBuffer.append("")
				if coCorrespondingAuthorIndexes:
					correspondingAuthorStrings = []
					for authorIndex in coCorrespondingAuthorIndexes:
						author = authors[authorIndex]
						authorName = author["name"] if "name" in author and isinstance(author["name"], str) else ""
						emails = Templates._getEmails(author)
						correspondingAuthorStrings.append(
							"{0}{1}".format(authorName, " ({0})".format(", ".join(emails)) if emails else "")
						)
					stringBuffer.append("\\corres{{Corresponding author{0}: {1}}}".format(
						"s" if len(coCorrespondingAuthorIndexes) >= 2 else "", Templates._joinAuthors(correspondingAuthorStrings)
					))
					stringBuffer.append("")

				# Abstract #
				abstractBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("abstract"), "^.*\\.tex$", doubleLineSeparators = False
				)
				if abstractBuffer:
					stringBuffer.append("\\abstract[Abstract]{{{0}}}".format(" ".join(abstractBuffer)))
					stringBuffer.append("")

				# Keywords #
				if "keywords" in kwargs:
					if isinstance(kwargs["keywords"], (tuple, list)) and kwargs["keywords"]:
						stringBuffer.append("\\keywords{{{0}}}".format(Templates.Wiley.KeywordSeparator.join(kwargs["keywords"])))
						stringBuffer.append("")
					elif isinstance(kwargs["keywords"], str):
						stringBuffer.append("\\keywords{{{0}}}".format(kwargs["keywords"]))
						stringBuffer.append("")
				stringBuffer.extend(["\\maketitle", ""])
				if coFirstAuthorIndexes:
					coFirstAuthorNames = [
						authors[authorIndex].get("name", "") for authorIndex in coFirstAuthorIndexes
					]
					stringBuffer.extend([
						"\\renewcommand\\thefootnote{}",
						"\\footnotetext{{{0} are the co-first authors contributing equally to this work. }}".format(
							Templates._joinAuthors(coFirstAuthorNames)
						), "",
						"\\renewcommand\\thefootnote{\\fnsymbol{footnote}}",
						"\\setcounter{footnote}{1}", ""
					])

				# TeX #
				stringBuffer.extend(Templates._readSources(
					baseDirectoryPath, kwargs.get("tex"), "^.*\\.tex$", separateSources = True
				))

				# Bib #
				dictionary = {}
				bibBuffer = Templates._readSources(
					baseDirectoryPath, kwargs.get("bib"), "^.*\\.bib$", separateSources = True
				)
				if bibBuffer:
					dictionary["ref.bib"] = bibBuffer
					stringBuffer.extend(["\\bibliography{ref.bib}", ""])
				stringBuffer.append("\\end{document}")
				dictionary[targetFileName] = stringBuffer
				return dictionary
