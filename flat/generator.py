from os import chdir, getcwd, makedirs
from os.path import split
from sys import executable, exit
from shutil import rmtree
from codecs import lookup
from copy import deepcopy
from json import dump, loads
from tkinter import Button, Entry, Frame, Label, Listbox, StringVar, Tk
from tkinter.filedialog import askdirectory
from tkinter.font import Font, families
from tkinter.messagebox import askokcancel, showerror
from tkinter.ttk import Style, Treeview
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Generator:
	__DefaultFilePath, __Version, __DefaultEncoding = "metadata.json", 20260312, "utf-8"
	__Packages = [
		"\\usepackage{amsmath, amssymb, amsfonts}", "\\usepackage{bm}", "\\usepackage{xcolor}", "\\usepackage{graphicx}", "\\usepackage{enumitem}", 
		"\\usepackage{booktabs}", "\\usepackage{multirow}", "\\usepackage{threeparttable}", "\\usepackage{algorithm}", "\\usepackage{algpseudocode}", 
		"\\usepackage[numbers,sort&compress]{natbib}", "\\usepackage{xurl}", "\\usepackage{flushend}"
	]
	__DefaultTitle, __DefaultKeywords = "Title", ["LaTeX", "Typesetting", "Acceptance"]
	__DefaultTargets = ["ACMConference", "Elsevier", "IEEEConference", "IEEEJournal", "MDPI", "Nature", "Springer", "TSP", "Wiley"]
	__DefaultMetadata = {"version":__Version, "metadataEncoding":__DefaultEncoding, "targetEncoding":__DefaultEncoding, "packages":deepcopy(__Packages), "title":__DefaultTitle, "authors":[
		{"name":"San Zhang", "affiliations":["Affiliation A", "Affiliation B", "Affiliation C"], "FA":True, "CA":False, "email":"sanzhang@gmail.com", "ORCID":"0000-0000-0000-0003"}, 
		{"name":"Si Li", "affiliations":["Affiliation A", "Affiliation B"], "FA":True, "CA":False, "email":"sili@gmail.com", "ORCID":"0000-0000-0000-0004"}, 
		{"name":"Wu Wang", "affiliations":["Affiliation A"], "FA":False, "CA":False, "email":"wuwang@gmail.com", "ORCID":"0000-0000-0000-0005"}, 
		{"name":"Liu Zhao", "affiliations":["Affiliation A"], "FA":False, "CA":True, "email":"liuzhao@gmail.com", "ORCID":"0000-0000-0000-0006"}, 
		{"name":"Qi Sun", "affiliations":["Affiliation A"], "FA":False, "CA":True, "email":"qisun@gmail.com", "ORCID":"0000-0000-0000-0007"}
	], "abstractPath":"content/abstract.tex", "keywords":deepcopy(__DefaultKeywords), "contentPaths":["content/{0}.tex".format(count) for count in range(1, 7)], "targets":__DefaultTargets}
	def __init__(self:object, filePath:str = __DefaultFilePath) -> object:
		self.__filePath = filePath if isinstance(filePath, str) else Generator.__DefaultFilePath
		self.clear()
		self.load()
	def clear(self:object) -> None:
		self.__metadata = {
			"version":Generator.__Version, "metadataEncoding":"", "targetEncoding":"", "packages":[], 
			"title":"", "authors":[], "abstractPath":"", "keywords":[], "contentPaths":[], "targets":[]
		}
	def load(self:object) -> bool|BaseException:
		try:
			with open(self.__filePath, "rb") as f:
				binaryStrings = f.read()
			if b"metadataEncoding" in binaryStrings:
				metadataEncodingIndex, binaryStringLength, metadataEncodingBuffer = binaryStrings.index(b"metadataEncoding"), len(binaryStrings), []
				while metadataEncodingIndex < binaryStringLength:
					if binaryStrings[metadataEncodingIndex] in (45, 46, 95) or 65 <= binaryStrings[metadataEncodingIndex] <= 90 or 97 <= binaryStrings[metadataEncodingIndex] <= 122:
						metadataEncodingBuffer.append(chr(binaryStrings[metadataEncodingIndex]))
					elif metadataEncodingBuffer:
						break
					metadataEncodingIndex += 1
				metadataEncoding = "".join(metadataEncodingBuffer)
				del metadataEncodingIndex, binaryStringLength, metadataEncodingBuffer
				try:
					lookup(metadataEncoding)
				except:
					metadataEncoding = Generator.__DefaultEncoding
			else:
				metadataEncoding = Generator.__DefaultEncoding
			d, status = loads(binaryStrings.decode(metadataEncoding)), True
			if "metadataEncoding" in d and isinstance(d["metadataEncoding"], str):
				self.__metadata["metadataEncoding"] = d["metadataEncoding"]
			else:
				status = False
			if "targetEncoding" in d and isinstance(d["targetEncoding"], str):
				self.__metadata["targetEncoding"] = d["targetEncoding"]
			else:
				status = False
			if "packages" in d and isinstance(d["packages"], (tuple, list)):
				self.__metadata["packages"].clear()
				for package in d["packages"]:
					if isinstance(package, str):
						self.__metadata["packages"].append(package)
					else:
						status = False
			else:
				status = False
			if "title" in d and isinstance(d["title"], str):
				self.__metadata["title"] = d["title"]
			else:
				status = False
			if "authors" in d and isinstance(d["authors"], (tuple, list)):
				self.__metadata["authors"].clear()
				for author in d["authors"]:
					if isinstance(author, dict) and (
						"name" in author and isinstance(author["name"], str) and "affiliations" in author and isinstance(author["affiliations"], (tuple, list))
						and all(isinstance(affiliation, str) for affiliation in author["affiliations"])
						and "FA" in author and isinstance(author["FA"], bool) and "CA" in author and isinstance(author["CA"], bool)
					):
						self.__metadata["authors"].append(author)
					else:
						status = False
			else:
				status = False
			if "abstractPath" in d and isinstance(d["abstractPath"], str):
				self.__metadata["abstractPath"] = d["abstractPath"]
			else:
				status = False
			if "keywords" in d and isinstance(d["keywords"], (tuple, list)):
				self.__metadata["keywords"].clear()
				for keyword in d["keywords"]:
					if isinstance(keyword, str):
						self.__metadata["keywords"].append(keyword)
					else:
						status = False
			else:
				status = False
			if "contentPaths" in d and isinstance(d["contentPaths"], (tuple, list)):
				self.__metadata["contentPaths"].clear()
				for contentPath in d["contentPaths"]:
					if isinstance(contentPath, str):
						self.__metadata["contentPaths"].append(contentPath)
					else:
						status = False
			else:
				status = False
			return status
		except BaseException as e:
			return e
	def getMetadata(self:object) -> dict:
		return deepcopy(self.__metadata)
	def setDefault(self:object) -> None:
		self.__metadata = deepcopy(Generator.__DefaultMetadata)
	def save(self:object) -> bool|BaseException:
		try:
			makedirs(split(self.__filePath)[0])
			with open(self.__filePath, "w", encoding = self.__metadata["metadataEncoding"]) as f:
				dump(self.__metadata, f, indent = "\t", sort_keys = True)
			return True
		except BaseException as e:
			return e
	def set(self:object, key:str, value:object) -> bool:
		if "filePath" == key:
			if isinstance(value, str):
				self.__filePath = value
				return True
		elif "metadataEncoding" == key:
			if isinstance(value, str):
				self.__metadata["metadataEncoding"] = value
				return True
		elif "targetEncoding" == key:
			if isinstance(value, str):
				self.__metadata["targetEncoding"] = value
				return True
		return False
	def generate(self:object) -> dict:
		results = {}
		for target in self.__metadata["targets"]:
			results[target] = None
		return results
	@staticmethod
	def getDefaultFilePath() -> str:
		return Generator.__DefaultFilePath
	@staticmethod
	def getVersion() -> int:
		return Generator.__Version
	@staticmethod
	def computeWordCount(string:str) -> int|str:
		if isinstance(string, str) and string.isprintable():
			if string.startswith(" ") or string.endswith(" "):
				return "Not a stripped string"
			else:
				stringIndex, stringCount, stack, letterDigitFlag, wordCount = 0, len(string), [], False, 0
				while stringIndex < stringCount:
					if '$' == string[stringIndex]:
						stringIndex += 1
						if stringIndex < stringCount and '$' == string[stringIndex]:
							if stack and "$$" == stack[-1]:
								stack.pop()
							else:
								stack.append("$$")
							stringIndex += 1
						else:
							if stack and "$" == stack[-1]:
								stack.pop()
							else:
								stack.append("$")
					elif '\\' == string[stringIndex]:
						stringIndex += 1
						if stringIndex < stringCount:
							if '(' == string[stringIndex]:
								stack.append("\\(")
								stringIndex += 1
							elif '[' == string[stringIndex]:
								stack.append("\\[")
								stringIndex += 1
							elif ')' == string[stringIndex]:
								if stack and "\\(" == stack[-1]:
									stack.pop()
									stringIndex += 1
								else:
									return "Unmatched \\)"
							elif ']' == string[stringIndex]:
								if stack and "\\[" == stack[-1]:
									stack.pop()
									stringIndex += 1
								else:
									return "Unmatched \\]"
							elif string[stringIndex] in ('$', '{', '}'):
								stringIndex += 1
					elif '{' == string[stringIndex]:
						stack.append("{")
						stringIndex += 1
					elif '}' == string[stringIndex]:
						if stack and "{" == stack[-1]:
							stack.pop()
							stringIndex += 1
						else:
							return "Unmatched }"
					elif ' ' == string[stringIndex]:
						stringIndex += 1
						if stringIndex < stringCount and ' ' == string[stringIndex]:
							return "Continuous spaces"
						elif letterDigitFlag:
							letterDigitFlag = False
							wordCount += 1
					elif 'A' <= string[stringIndex] <= 'Z' or 'a' <= string[stringIndex] <= 'z' or '0' <= string[stringIndex] <= '9':
						letterDigitFlag = True
						stringIndex += 1
					else:
						stringIndex += 1
				if stack:
					if 1 == len(stack):
						return "Unclosed {0}".format(stack[0])
					else:
						return "{0} environments unclosed".format(len(stack))
				else:
					return wordCount + 1 if letterDigitFlag else wordCount
		else:
			return "Not a printable string"

class GraphicalUserInterface:
	__DefaultPaddingValue, __DefaultBorderWidth, __DefaultFontFamily = 5, 2, "Times New Roman"
	__UnavailableTitleWordCountPrompt, __RecommendedMinimumTitleWordCount, __RecommendedMaximumTitleWordCount = "N/A", 3, 15
	def __init__(self, filePath:str = Generator.getDefaultFilePath(), paddingValue:int = __DefaultPaddingValue, borderWidth:int = __DefaultBorderWidth, fontFamily:str = __DefaultFontFamily) -> object:
		self.__filePath = filePath if isinstance(filePath, str) else Generator.getDefaultFilePath()
		self.__generator = Generator(self.__filePath)
		self.__paddingValue = paddingValue if isinstance(paddingValue, int) and paddingValue >= 1 else GraphicalUserInterface.__DefaultPaddingValue
		self.__borderWidth = borderWidth if isinstance(borderWidth, int) and borderWidth >= 1 else GraphicalUserInterface.__borderWidth
		
		# Tk #
		self.__root = Tk()
		self.__windowTitle = "Generator_v{0}".format(Generator.getVersion())
		self.__root.title(self.__windowTitle)
		self.__root.resizable(0, 0)
		self.__root.geometry()
		self.__root.protocol("WM_DELETE_WINDOW", lambda:self.__onClosingWindow())
		if isinstance(fontFamily, str):
			fontFamilyLower = fontFamily.lower()
			for family in families():
				if family.lower() == fontFamilyLower:
					self.__fontFamily = fontFamily
					break
			else:
				self.__fontFamily = GraphicalUserInterface.__DefaultFontFamily
			del fontFamilyLower, family
		else:
			self.__fontFamily = GraphicalUserInterface.__DefaultFontFamily
		self.__font = Font(family = self.__fontFamily, size = 12)
		frame = Frame(self.__root)
		frame.pack(side = "top", fill = "both", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(frame, text = "Generator", font = Font(family = self.__fontFamily, size = 16, weight = "bold"), fg = "red", anchor = "center", justify = "center").pack(
			side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue
		)
		
		# Paths and Encoding #
		pathEncodingFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		pathEncodingFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(pathEncodingFrame, text = "Executable path: ", font = self.__font).grid(row = 0, column = 0, sticky = "e")
		executablePathStringVar = StringVar()
		executablePathStringVar.set(executable)
		executablePathEntry = Entry(pathEncodingFrame, text = executablePathStringVar, font = self.__font, width = 40, state = "readonly")
		executablePathEntry.grid(row = 0, column = 1, columnspan = 4, sticky = "w")
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 5)
		Label(pathEncodingFrame, text = "Script path: ", font = self.__font).grid(row = 0, column = 6, sticky = "e")
		scriptPathStringVar = StringVar()
		scriptPathStringVar.set(__file__)
		scriptPathEntry = Entry(pathEncodingFrame, text = scriptPathStringVar, font = self.__font, width = 30, state = "readonly")
		scriptPathEntry.grid(row = 0, column = 7, columnspan = 2, sticky = "w")
		self.__workingDirectoryLabel = Label(pathEncodingFrame, text = "Working directory: ", font = self.__font, fg = "green")
		self.__workingDirectoryLabel.grid(row = 1, column = 0, sticky = "e")
		self.__workingDirectoryStringVar = StringVar()
		self.__workingDirectoryStringVar.set(getcwd())
		self.__workingDirectoryStringVar.trace_add(("write", "unset"), lambda *args:self.__workingDirectoryLabel.config(text = "Working directory*: ", fg = "orange"))
		self.__workingDirectoryEntry = Entry(pathEncodingFrame, text = self.__workingDirectoryStringVar, font = self.__font, width = 30)
		self.__workingDirectoryEntry.grid(row = 1, column = 1, columnspan = 3, sticky = "w")
		self.__workingDirectoryButton = Button(pathEncodingFrame, text = "...", font = self.__font, command = self.__browseWorkingDirectory)
		self.__workingDirectoryButton.grid(row = 1, column = 4, sticky = "e")
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 1, column = 5)
		Label(pathEncodingFrame, text = "Metadata file path: ", font = self.__font).grid(row = 1, column = 6, sticky = "e")
		self.__filePathStringVar = StringVar()
		self.__filePathStringVar.set(self.__filePath)
		self.__filePathStringVar.trace_add(("write", "unset"), lambda *args:self.__generator.set("filePath", self.__filePathStringVar.get()))
		self.__filePathEntry = Entry(pathEncodingFrame, text = self.__filePathStringVar, font = self.__font, width = 30)
		self.__filePathEntry.grid(row = 1, column = 7, columnspan = 2, sticky = "w")
		Label(pathEncodingFrame, text = "Metadata encoding: ", font = self.__font).grid(row = 2, column = 0, sticky = "e")
		self.__metadataEncodingStringVar = StringVar()
		self.__metadataEncodingStringVar.trace_add(("write", "unset"), lambda *args:self.__generator.set("metadataEncoding", self.__metadataEncodingStringVar.get()))
		self.__metadataEncodingEntry = Entry(pathEncodingFrame, text = self.__metadataEncodingStringVar, font = self.__font, width = 10)
		self.__metadataEncodingEntry.grid(row = 2, column = 1, sticky = "w")
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 2, column = 2)
		Label(pathEncodingFrame, text = "Target encoding: ", font = self.__font).grid(row = 2, column = 3, sticky = "e")
		self.__targetEncodingStringVar = StringVar()
		self.__targetEncodingStringVar.trace_add(("write", "unset"), lambda *args:self.__generator.set("targetEncoding", self.__targetEncodingStringVar.get()))
		self.__targetEncodingEntry = Entry(pathEncodingFrame, text = self.__targetEncodingStringVar, font = self.__font, width = 10)
		self.__targetEncodingEntry.grid(row = 2, column = 4, sticky = "w")
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 2, column = 5)
		self.__metadataLoaderButton = Button(pathEncodingFrame, text = "Load metadata", font = self.__font, command = lambda:(self.__generator.load(), self.__update()))
		self.__metadataLoaderButton.grid(row = 2, column = 6)
		self.__defaultSetterButton = Button(pathEncodingFrame, text = "Set default", font = self.__font, command = lambda:(self.__generator.setDefault(), self.__update()))
		self.__defaultSetterButton.grid(row = 2, column = 7)
		self.__metadataSaverButton = Button(pathEncodingFrame, text = "Save metadata", font = self.__font, command = self.__save)
		self.__metadataSaverButton.grid(row = 2, column = 8)
		
		# Title #
		titleFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		titleFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(titleFrame, text = "Title: ", font = self.__font).grid(row = 0, column = 0)
		self.__titleStringVar = StringVar()
		self.__titleStringVar.trace_add(("write", "unset"), self.__onChangingTitle)
		self.__titleEntry = Entry(titleFrame, text = self.__titleStringVar, font = self.__font, width = 60)
		self.__titleEntry.grid(row = 0, column = 1)
		Label(titleFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 2)
		Label(titleFrame, text = "Title word count: ", font = self.__font).grid(row = 0, column = 3)
		self.__titleWordCountLabel = Label(titleFrame, text = GraphicalUserInterface.__UnavailableTitleWordCountPrompt, font = self.__font, fg = "red")
		self.__titleWordCountLabel.grid(row = 0, column = 4)
		
		# Packages, Abstract, and Keywords #
		packageAbstractKeywordFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		packageAbstractKeywordFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(packageAbstractKeywordFrame, text = "Packages: ", font = self.__font).grid(row = 0, column = 0, rowspan = 2)
		self.__packageListbox = Listbox(packageAbstractKeywordFrame, font = self.__font, width = 40, height = 8, selectmode = "extended", exportselection = False)
		self.__packageListbox.grid(row = 0, column = 1, rowspan = 2)
		Label(packageAbstractKeywordFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 2, rowspan = 2)
		Label(packageAbstractKeywordFrame, text = "Abstract file path: ", font = self.__font).grid(row = 0, column = 3)
		self.__abstractPathEntry = Entry(packageAbstractKeywordFrame, font = self.__font, width = 30)
		self.__abstractPathEntry.grid(row = 0, column = 4)
		Label(packageAbstractKeywordFrame, text = " ", font = self.__font).grid(row = 0, column = 5)
		self.__abstractPathButton = Button(packageAbstractKeywordFrame, text = "Edit", font = self.__font)
		self.__abstractPathButton.grid(row = 0, column = 6)
		Label(packageAbstractKeywordFrame, text = "Keywords: ", font = self.__font).grid(row = 1, column = 3)
		self.__keywordListbox = Listbox(packageAbstractKeywordFrame, font = self.__font, width = 20, height = 5, selectmode = "extended", exportselection = False)
		self.__keywordListbox.grid(row = 1, column = 4, columnspan = 3)
		
		# Authors #
		authorFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		authorFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(authorFrame, text = "Authors: ", font = self.__font).grid(row = 0, column = 0)
		style = Style()
		style.configure("Custom.Treeview", font = self.__font, rowheight = 18)
		style.configure("Custom.Treeview.Heading", font = (self.__fontFamily, 12, "bold"))
		self.__authorTreeview = Treeview(authorFrame, columns=("Name", "Affilications", "FA", "CA"), show = "headings", height = 8)
		self.__authorTreeview.configure(style = "Custom.Treeview")
		self.__authorTreeview.heading("Name", text = "Name")
		self.__authorTreeview.heading("Affilications", text = "Affilications")
		self.__authorTreeview.heading("FA", text = "FA")
		self.__authorTreeview.heading("CA", text = "CA")
		self.__authorTreeview.column("Name", width = 150, anchor = "center")
		self.__authorTreeview.column("Affilications", width = 100, anchor = "center")
		self.__authorTreeview.column("FA", width = 50, anchor = "center")
		self.__authorTreeview.column("CA", width = 50, anchor = "center")
		self.__authorTreeview.grid(row = 0, column = 1)
		Label(authorFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 2)
		Label(authorFrame, text = "Affiliations: ", font = self.__font).grid(row = 0, column = 3)
		self.__affiliationListbox = Listbox(authorFrame, font = self.__font, width = 30, height = 8, selectmode = "extended", exportselection = False)
		self.__affiliationListbox.grid(row = 0, column = 4)
		
		# Content #
		
		# Mainloop #
		self.__update()
		self.__root.mainloop()
	def __onClosingWindow(self:object) -> None:
		if askokcancel(self.__windowTitle, "Are you sure that you want to exit? ", icon = "question"):
			self.__root.destroy()
	def __browseWorkingDirectory(self:object) -> None:
		workingDirectory = askdirectory(title = self.__windowTitle + " - Select the working directory", initialdir = getcwd(), mustexist = True)
		if workingDirectory:
			try:
				chdir(workingDirectory)
			except BaseException as e:
				showerror(self.__windowTitle, "Failed to change the working directory to {0} due to {1}. ".format(repr(workingDirectory), repr(status)))
	def __save(self:object) -> None:
		status = self.__generator.save()
		if isinstance(status, BaseException):
			showerror(self.__windowTitle, "Failed to save to {0} due to {1}. ".format(repr(self.__filePath), repr(status)))
		elif True == status:
			self.__root.title(self.__windowTitle)
	def __onChangingTitle(self:object, *args:tuple) -> None:
		wordCount = Generator.computeWordCount(self.__titleStringVar.get())
		if isinstance(wordCount, str):
			self.__titleWordCountLabel.config(text = wordCount, fg = "red")
		elif isinstance(wordCount, int):
			if GraphicalUserInterface.__RecommendedMinimumTitleWordCount <= wordCount <= GraphicalUserInterface.__RecommendedMaximumTitleWordCount:
				self.__titleWordCountLabel.config(text = str(wordCount), fg = "green")
			else:
				self.__titleWordCountLabel.config(text = str(wordCount), fg = "orange")
		else:
			self.__titleWordCountLabel.config(text = GraphicalUserInterface.__UnavailableTitleWordCountPrompt, fg = "red")
	def __disable(self:object) -> None:
		self.__metadataEncodingEntry.config(state = "disabled")
		self.__targetEncodingEntry.config(state = "disabled")
		self.__titleEntry.config(state = "disabled")
	def __enable(self:object) -> None:
		self.__metadataEncodingEntry.config(state = "enabled")
		self.__targetEncodingEntry.config(state = "enabled")
		self.__titleEntry.config(state = "enabled")
	def __update(self:object) -> None:
		d = self.__generator.getMetadata()
		if "metadataEncoding" in d:
			self.__metadataEncodingStringVar.set(d["metadataEncoding"])
		if "targetEncoding" in d:
			self.__targetEncodingStringVar.set(d["targetEncoding"])
		if "title" in d:
			self.__titleStringVar.set(d["title"])
		if "packages" in d:
			self.__packageListbox.delete(0, "end")
			for package in d["packages"]:
				self.__packageListbox.insert("end", package.strip())
		if "abstractPath" in d:
			self.__abstractPathEntry.delete(0, "end")
			self.__abstractPathEntry.insert(0, d["abstractPath"])
		if "keywords" in d:
			self.__keywordListbox.delete(0, "end")
			for keyword in d["keywords"]:
				self.__keywordListbox.insert("end", keyword.strip())
		if "authors" in d:
			self.__authorTreeview.delete(*self.__authorTreeview.get_children())
			self.__affiliationListbox.delete(0, "end")
			affiliations = []
			for author in d["authors"]:
				if isinstance(author, dict):
					affiliationIDs = []
					if "affiliations" in author and isinstance(author["affiliations"], (tuple, list)):
						for affiliation in author["affiliations"]:
							affiliationStripped = affiliation.strip()
							if affiliationStripped not in affiliations:
								affiliations.append(affiliationStripped)
							affiliationIDs.append(affiliations.index(affiliationStripped))
					self.__authorTreeview.insert("", "end", values = (
						author["name"] if "name" in author and isinstance(author["name"], str) else "", "; ".join(str(affiliationID) for affiliationID in affiliationIDs), 
						"☑" if "FA" in author and isinstance(author["FA"], bool) and author["FA"] else "☐", 
						"☑" if "CA" in author and isinstance(author["CA"], bool) and author["CA"] else "☐", 
					))
			for affiliation in affiliations:
				self.__affiliationListbox.insert("end", affiliation)


def main() -> int:
	graphicalUserInterface = GraphicalUserInterface()
	return EXIT_SUCCESS



if "__main__" == __name__:
	exit(main())