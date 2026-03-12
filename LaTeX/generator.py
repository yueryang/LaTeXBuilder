from os import getcwd, makedirs
from sys import executable, exit
from shutil import rmtree
from codecs import lookup
from copy import deepcopy
from json import dump, loads
from tkinter import Button, Entry, Frame, Label, Listbox, StringVar, Tk
from tkinter.font import Font, families
from tkinter.messagebox import askokcancel
from tkinter.ttk import Style, Treeview
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class Metadata:
	__DefaultFilePath, __Version, __DefaultEncoding = "metadata.json", 20260312, "utf-8"
	__Packages = [
		"\\usepackage{amsmath, amssymb, amsfonts}", "\\usepackage{bm}", "\\usepackage{xcolor}", "\\usepackage{graphicx}", "\\usepackage{enumitem}", 
		"\\usepackage{booktabs}", "\\usepackage{multirow}", "\\usepackage{threeparttable}", "\\usepackage{algorithm}", "\\usepackage{algpseudocode}", 
		"\\usepackage[numbers,sort&compress]{natbib}", "\\usepackage{xurl}", "\\usepackage{flushend}"
	]
	__DefaultTitle, __DefaultKeywords = "Title", ["LaTeX", "Typesetting", "Acceptance"]
	__DefaultTargets = ["ACMConference", "Elsevier", "IEEEConference", "IEEEJournal", "MDPI", "Nature", "Springer", "TSP", "Wiley"]
	__DefaultDict = {"version":__Version, "metadataEncoding":__DefaultEncoding, "targetEncoding":__DefaultEncoding, "packages":deepcopy(__Packages), "title":__DefaultTitle, "authors":[
		{"name":"San Zhang", "affiliations":["Affiliation A", "Affiliation B", "Affiliation C"], "FA":True, "CA":False, "email":"sanzhang@gmail.com", "ORCID":"0000-0000-0000-0003"}, 
		{"name":"Si Li", "affiliations":["Affiliation A", "Affiliation B"], "FA":True, "CA":False, "email":"sili@gmail.com", "ORCID":"0000-0000-0000-0004"}, 
		{"name":"Wu Wang", "affiliations":["Affiliation A"], "FA":False, "CA":False, "email":"wuwang@gmail.com", "ORCID":"0000-0000-0000-0005"}, 
		{"name":"Liu Zhao", "affiliations":["Affiliation A"], "FA":False, "CA":True, "email":"liuzhao@gmail.com", "ORCID":"0000-0000-0000-0006"}, 
		{"name":"Qi Sun", "affiliations":["Affiliation A"], "FA":False, "CA":True, "email":"qisun@gmail.com", "ORCID":"0000-0000-0000-0007"}
	], "abstractPath":"content/abstract.tex", "keywords":deepcopy(__DefaultKeywords), "contentPaths":["content/{0}.tex".format(count) for count in range(1, 7)], "targets":__DefaultTargets}
	def __init__(self:object, filePath:str = __DefaultFilePath) -> object:
		self.__filePath = filePath if isinstance(filePath, str) else Metadata.__DefaultFilePath
		self.clear()
		self.load()
	def clear(self:object) -> None:
		self.__metadata = {
			"version":Metadata.__Version, "metadataEncoding":"", "targetEncoding":"", 
			"packages":[], "title":"", "authors":[], "abstractPath":"", "keywords":[], "contentPaths":[]
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
					metadataEncoding = Metadata.__DefaultEncoding
			else:
				metadataEncoding = Metadata.__DefaultEncoding
			d, status = loads(binaryStrings.decode(metadataEncoding)), True
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
	def getDict(self:object) -> dict:
		return deepcopy(self.__metadata)
	def setDefault(self:object) -> None:
		self.__metadata = deepcopy(Metadata.__DefaultDict)
	def save(self:object) -> bool|BaseException:
		try:
			with open(self.__filePath, "w", encoding = self.__metadata["metadataEncoding"]) as f:
				dump(self.__metadata, f, indent = "\t", sort_keys = True)
			return True
		except BaseException as e:
			return e
	@staticmethod
	def getDefaultFilePath() -> str:
		return Metadata.__DefaultFilePath
	@staticmethod
	def getVersion() -> int:
		return Metadata.__Version

class GraphicalUserInterface:
	__DefaultPaddingValue, __DefaultBorderWidth, __DefaultFontFamily = 5, 2, "Times New Roman"
	def __init__(self, filePath:str = Metadata.getDefaultFilePath(), paddingValue:int = __DefaultPaddingValue, borderWidth:int = __DefaultBorderWidth, fontFamily:str = __DefaultFontFamily) -> object:
		self.__filePath = filePath if isinstance(filePath, str) else Metadata.getDefaultFilePath()
		self.__metadata = Metadata(self.__filePath)
		self.__paddingValue = paddingValue if isinstance(paddingValue, int) and paddingValue >= 1 else GraphicalUserInterface.__DefaultPaddingValue
		self.__borderWidth = borderWidth if isinstance(borderWidth, int) and borderWidth >= 1 else GraphicalUserInterface.__borderWidth
		
		# Tk #
		self.__root = Tk()
		self.__root.title("Generator (v{0})".format(Metadata.getVersion()))
		self.__root.resizable(0, 0)
		self.__root.geometry()
		self.__root.protocol("WM_DELETE_WINDOW", lambda:self.__onWM_DELETE_WINDOW())
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
		executablePathEntry.grid(row = 0, column = 1, columnspan = 4)
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 5)
		Label(pathEncodingFrame, text = "Script path: ", font = self.__font).grid(row = 0, column = 6, sticky = "e")
		scriptPathStringVar = StringVar()
		scriptPathStringVar.set(__file__)
		scriptPathEntry = Entry(pathEncodingFrame, text = scriptPathStringVar, font = self.__font, width = 30, state = "readonly")
		scriptPathEntry.grid(row = 0, column = 7, columnspan = 2)
		Label(pathEncodingFrame, text = "Working directory: ", font = self.__font).grid(row = 1, column = 0, sticky = "e")
		self.__workingDirectoryStringVar = StringVar()
		self.__workingDirectoryStringVar.set(getcwd())
		self.__workingDirectoryEntry = Entry(pathEncodingFrame, text = self.__workingDirectoryStringVar, font = self.__font, width = 40)
		self.__workingDirectoryEntry.grid(row = 1, column = 1, columnspan = 4)
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 1, column = 5)
		Label(pathEncodingFrame, text = "Metadata file path: ", font = self.__font).grid(row = 1, column = 6, sticky = "e")
		self.__filePathStringVar = StringVar()
		self.__filePathStringVar.set(self.__filePath)
		self.__filePathEntry = Entry(pathEncodingFrame, text = self.__filePathStringVar, font = self.__font, width = 30)
		self.__filePathEntry.grid(row = 1, column = 7, columnspan = 2)
		Label(pathEncodingFrame, text = "Metadata encoding: ", font = self.__font).grid(row = 2, column = 0, sticky = "e")
		self.__metadataEncodingStringVar = StringVar()
		self.__metadataEncodingEntry = Entry(pathEncodingFrame, text = self.__metadataEncodingStringVar, font = self.__font, width = 10)
		self.__metadataEncodingEntry.grid(row = 2, column = 1)
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 2, column = 2)
		Label(pathEncodingFrame, text = "Target encoding: ", font = self.__font).grid(row = 2, column = 3, sticky = "e")
		self.__targetEncodingStringVar = StringVar()
		self.__targetEncodingEntry = Entry(pathEncodingFrame, text = self.__targetEncodingStringVar, font = self.__font, width = 10)
		self.__targetEncodingEntry.grid(row = 2, column = 4)
		Label(pathEncodingFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 2, column = 5)
		self.__metadataLoaderButton = Button(pathEncodingFrame, text = "Load metadata", font = self.__font)
		self.__metadataLoaderButton.grid(row = 2, column = 6)
		self.__defaultSetterButton = Button(pathEncodingFrame, text = "Set default", font = self.__font)
		self.__defaultSetterButton.grid(row = 2, column = 7)
		self.__metadataSaverButton = Button(pathEncodingFrame, text = "Save metadata", font = self.__font)
		self.__metadataSaverButton.grid(row = 2, column = 8)
		
		# Title and Encoding #
		titleEncodingFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		titleEncodingFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(titleEncodingFrame, text = "Title: ", font = self.__font).grid(row = 0, column = 0)
		self.__titleEntry = Entry(titleEncodingFrame, font = self.__font, width = 70)
		self.__titleEntry.grid(row = 0, column = 1)
		
		# Packages, Abstract, and Keywords #
		packageAbstractKeywordFrame = Frame(frame, relief = "raised", borderwidth = self.__borderWidth)
		packageAbstractKeywordFrame.pack(side = "top", fill = "x", expand = True, padx = self.__paddingValue, pady = self.__paddingValue)
		Label(packageAbstractKeywordFrame, text = "Packages: ", font = self.__font).grid(row = 0, column = 0, rowspan = 2)
		self.__packageListbox = Listbox(packageAbstractKeywordFrame, font = self.__font, width = 40, height = 8, selectmode = "extended", exportselection = False)
		self.__packageListbox.grid(row = 0, column = 1, rowspan = 2)
		Label(packageAbstractKeywordFrame, text = " " * self.__paddingValue, font = self.__font).grid(row = 0, column = 2, rowspan = 2)
		Label(packageAbstractKeywordFrame, text = "Abstract file path: ", font = self.__font).grid(row = 0, column = 3)
		self.__abstractPathEntry = Entry(packageAbstractKeywordFrame, font = self.__font, width = 20)
		self.__abstractPathEntry.grid(row = 0, column = 4)
		self.__abstractPathButton = Button(packageAbstractKeywordFrame, text = "Edit", font = self.__font)
		self.__abstractPathButton.grid(row = 0, column = 5)
		Label(packageAbstractKeywordFrame, text = "Keywords: ", font = self.__font).grid(row = 1, column = 3)
		self.__keywordListbox = Listbox(packageAbstractKeywordFrame, font = self.__font, width = 20, height = 5, selectmode = "extended", exportselection = False)
		self.__keywordListbox.grid(row = 1, column = 4)
		
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
		self.__load()
		self.__root.mainloop()
	def __onWM_DELETE_WINDOW(self:object) -> None:
		if askokcancel("Generator (v{0})".format(Metadata.getVersion()), "Are you sure that you want to exit? ", icon = "question"):
			self.__root.destroy()
	def __disable(self:object) -> None:
		self.__titleEntry.config(state = "disabled")
		self.__targetEncodingEntry.config(state = "disabled")
	def __load(self:object) -> None:
		d = self.__metadata.getDict()
		if "metadataEncoding" in d:
			self.__metadataEncodingStringVar.set(d["metadataEncoding"])
		if "targetEncoding" in d:
			self.__targetEncodingStringVar.set(d["targetEncoding"])
		if "title" in d:
			self.__titleEntry.delete(0, "end")
			self.__titleEntry.insert(0, d["title"])
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