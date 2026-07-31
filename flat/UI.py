from __future__ import annotations

from codecs import lookup
from copy import deepcopy
from dataclasses import dataclass
from json import JSONDecodeError, dumps, loads
from os import fsync, replace
from pathlib import Path
from queue import Empty, Queue
from shutil import copy2
from subprocess import PIPE, STDOUT, Popen, TimeoutExpired
from sys import argv, executable
from tempfile import NamedTemporaryFile
from threading import Lock, Thread, current_thread
from typing import Any
try:
	import tkinter as tk
	from tkinter import filedialog, font as tkfont, messagebox, simpledialog, ttk
	TKINTER_IMPORT_ERROR:BaseException | None = None
except ImportError as error:
	tk = None
	filedialog = None
	tkfont = None
	messagebox = None
	simpledialog = None
	ttk = None
	TKINTER_IMPORT_ERROR = error


EXIT_SUCCESS = 0
EXIT_FAILURE = 1
DEFAULT_ENCODING = "utf-8"
DEFAULT_FONT_FAMILY = "Times New Roman"
DEFAULT_FONT_SIZE = 11
SOURCE_FIELDS = ("abstract", "tex", "bib", "figures")
LIST_FIELDS = ("authors", "abstract", "keywords", "packages", "tex", "bib", "figures", "targets")
TOP_LEVEL_FIELDS = {
	"abstract", "authors", "bib", "encoding", "figures", "keywords", "packages", "targets", "tex", "title", "version",
}
AUTHOR_FIELDS = {"name", "affiliations", "FA", "CA", "email", "ORCID"}
SOURCE_ITEM_FIELDS = {"type", "path", "encoding", "filter", "reverse", "text", "name", "base64"}
TARGET_FIELDS = {"template", "output"}
TEMPLATE_FIELDS = {"name", "category", "engine"}
OUTPUT_FIELDS = {"path", "type", "encoding", "newline"}


def default_metadata() -> dict[str, Any]:
	return {
		"abstract":[],
		"authors":[],
		"bib":[],
		"encoding":DEFAULT_ENCODING,
		"figures":[],
		"keywords":[],
		"packages":[],
		"targets":[],
		"tex":[],
		"title":"",
		"version":20260730,
	}


def merge_known(original:dict[str, Any], known_values:dict[str, Any]) -> dict[str, Any]:
	for key, value in known_values.items():
		if isinstance(value, dict) and isinstance(original.get(key), dict):
			merge_known(original[key], value)
		else:
			original[key] = deepcopy(value)
	return original


def author_summary(author:Any) -> str:
	if not isinstance(author, dict):
		return "Invalid author"
	name = author.get("name") if isinstance(author.get("name"), str) else "Unnamed author"
	affiliations = author.get("affiliations")
	affiliation_count = len(affiliations) if isinstance(affiliations, list) else 0
	flags = []
	if author.get("FA") is True:
		flags.append("co-first author")
	if author.get("CA") is True:
		flags.append("corresponding author")
	suffix = " · " + ", ".join(flags) if flags else ""
	return "{0} · {1} affiliation{2}{3}".format(
		name or "Unnamed author", affiliation_count, "" if affiliation_count == 1 else "s", suffix,
	)


def source_summary(source:Any) -> str:
	if not isinstance(source, dict):
		return "Invalid source"
	source_type = source.get("type", "unknown type")
	if source_type in ("file", "directory"):
		detail = source.get("path", "path not specified")
	elif source_type == "base64":
		detail = source.get("name", "file name not specified")
	else:
		text = source.get("text", "")
		detail = "{0} characters".format(len(text)) if isinstance(text, str) else "invalid text"
	return "{0} · {1}".format(source_type, detail)


def target_summary(target:Any) -> str:
	if not isinstance(target, dict):
		return "Invalid target"
	template = target.get("template") if isinstance(target.get("template"), dict) else {}
	output = target.get("output") if isinstance(target.get("output"), dict) else {}
	name = template.get("name", "?")
	category = template.get("category", "?")
	return "{0}.{1} → {2}".format(name, category, output.get("path", "path not specified"))


def unknown_field_count(data:Any) -> int:
	if not isinstance(data, dict):
		return 0
	count = len(set(data) - TOP_LEVEL_FIELDS)
	authors = data.get("authors")
	for author in authors if isinstance(authors, list) else []:
		if isinstance(author, dict):
			count += len(set(author) - AUTHOR_FIELDS)
	for field in SOURCE_FIELDS:
		sources = data.get(field)
		for source in sources if isinstance(sources, list) else []:
			if isinstance(source, dict):
				count += len(set(source) - SOURCE_ITEM_FIELDS)
	targets = data.get("targets")
	for target in targets if isinstance(targets, list) else []:
		if not isinstance(target, dict):
			continue
		count += len(set(target) - TARGET_FIELDS)
		template = target.get("template")
		output = target.get("output")
		if isinstance(template, dict):
			count += len(set(template) - TEMPLATE_FIELDS)
		if isinstance(output, dict):
			count += len(set(output) - OUTPUT_FIELDS)
	return count


def _detected_encoding(raw:bytes) -> str:
	if raw.startswith(b"\xef\xbb\xbf"):
		return "utf-8-sig"
	ascii_text = raw.decode("ascii", errors="ignore")
	marker = '"encoding"'
	index = ascii_text.find(marker)
	if index >= 0:
		colon = ascii_text.find(":", index + len(marker))
		first_quote = ascii_text.find('"', colon + 1)
		second_quote = ascii_text.find('"', first_quote + 1)
		if colon >= 0 and first_quote >= 0 and second_quote >= 0:
			candidate = ascii_text[first_quote + 1:second_quote]
			try:
				lookup(candidate)
				return candidate
			except LookupError:
				pass
	return DEFAULT_ENCODING


def load_json(file_path:Path | str) -> dict[str, Any]:
	path = Path(file_path)
	raw = path.read_bytes()
	encodings = []
	for encoding in (_detected_encoding(raw), "utf-8-sig", DEFAULT_ENCODING):
		if encoding not in encodings:
			encodings.append(encoding)
	last_error:BaseException | None = None
	for encoding in encodings:
		try:
			data = loads(raw.decode(encoding))
			if not isinstance(data, dict):
				raise ValueError("The root of metadata.json must be a JSON object.")
			return data
		except (UnicodeDecodeError, JSONDecodeError, ValueError) as error:
			last_error = error
	raise ValueError("Unable to read metadata.json: {0}".format(last_error))


@dataclass(frozen=True)
class ValidationIssue:
	severity:str
	field:str
	message:str


class MetadataValidationError(ValueError):
	def __init__(self, issues:list[ValidationIssue]) -> None:
		self.issues = issues
		super().__init__("The metadata contains {0} blocking errors.".format(len(issues)))


def _issue(issues:list[ValidationIssue], severity:str, field:str, message:str) -> None:
	issues.append(ValidationIssue(severity, field, message))


def _validate_source(
	issues:list[ValidationIssue],
	field:str,
	source:Any,
	base_directory:Path,
	allowed_types:tuple[str, ...],
) -> None:
	if not isinstance(source, dict):
		_issue(issues, "error", field, "A source entry must be a JSON object.")
		return
	source_type = source.get("type")
	if source_type not in allowed_types:
		_issue(issues, "error", field + ".type", "The source type must be one of: {0}.".format(", ".join(allowed_types)))
		return
	if source_type in ("directory", "file"):
		path_value = source.get("path")
		if not isinstance(path_value, str) or not path_value.strip():
			_issue(issues, "error", field + ".path", "A file or directory source must provide path.")
		else:
			resolved = Path(path_value)
			if not resolved.is_absolute():
				resolved = base_directory / resolved
			if source_type == "file" and not resolved.is_file():
				_issue(issues, "error", field + ".path", "The referenced file does not exist: {0}".format(path_value))
			elif source_type == "directory" and not resolved.is_dir():
				_issue(issues, "error", field + ".path", "The referenced directory does not exist: {0}".format(path_value))
	if source_type == "text" and not isinstance(source.get("text"), str):
		_issue(issues, "error", field + ".text", "A text source must provide a string value in text.")
	if source_type == "base64":
		if not isinstance(source.get("name"), str) or not source.get("name", "").strip():
			_issue(issues, "error", field + ".name", "A Base64 image must provide an output file name.")
		if not isinstance(source.get("base64"), str):
			_issue(issues, "error", field + ".base64", "A Base64 image must provide string content.")
	if "encoding" in source:
		try:
			lookup(source["encoding"])
		except (LookupError, TypeError):
			_issue(issues, "error", field + ".encoding", "The encoding name is invalid.")
	if "filter" in source and not isinstance(source["filter"], str):
		_issue(issues, "error", field + ".filter", "filter must be a string.")
	if "reverse" in source and not isinstance(source["reverse"], bool):
		_issue(issues, "error", field + ".reverse", "reverse must be a Boolean.")


def validate_metadata(data:Any, base_directory:Path | str) -> list[ValidationIssue]:
	issues:list[ValidationIssue] = []
	base_path = Path(base_directory)
	if not isinstance(data, dict):
		_issue(issues, "error", "$", "The root of metadata.json must be a JSON object.")
		return issues
	if not isinstance(data.get("title"), str):
		_issue(issues, "error", "title", "title must be a string.")
	else:
		word_count = len(data["title"].strip().split())
		if not 3 <= word_count <= 15:
			_issue(issues, "warning", "title", "A title of 3–15 English words is recommended.")
	if not isinstance(data.get("version"), int) or isinstance(data.get("version"), bool):
		_issue(issues, "error", "version", "version must be an integer.")
	encoding = data.get("encoding")
	if not isinstance(encoding, str):
		_issue(issues, "error", "encoding", "encoding must be a string.")
	else:
		try:
			lookup(encoding)
		except LookupError:
			_issue(issues, "error", "encoding", "encoding is not a valid codec name.")
	for field in LIST_FIELDS:
		if not isinstance(data.get(field), list):
			_issue(issues, "error", field, field + " must be an array.")
	for field in ("keywords", "packages"):
		value = data.get(field)
		if isinstance(value, list):
			for index, item in enumerate(value):
				if not isinstance(item, str):
					_issue(issues, "error", "{0}[{1}]".format(field, index), "The list item must be a string.")
	if isinstance(data.get("keywords"), list) and not data["keywords"]:
		_issue(issues, "warning", "keywords", "At least one keyword is recommended.")
	authors = data.get("authors")
	if isinstance(authors, list):
		if not authors:
			_issue(issues, "warning", "authors", "At least one author is recommended.")
		for index, author in enumerate(authors):
			field = "authors[{0}]".format(index)
			if not isinstance(author, dict):
				_issue(issues, "error", field, "An author entry must be a JSON object.")
				continue
			if not isinstance(author.get("name"), str) or not author.get("name", "").strip():
				_issue(issues, "error", field + ".name", "The author name must not be empty.")
			affiliations = author.get("affiliations")
			if not isinstance(affiliations, list) or not all(isinstance(value, str) for value in affiliations):
				_issue(issues, "error", field + ".affiliations", "affiliations must be an array of strings.")
			for boolean_field in ("FA", "CA"):
				if boolean_field in author and not isinstance(author[boolean_field], bool):
					_issue(issues, "error", field + "." + boolean_field, boolean_field + " must be a Boolean.")
			if not isinstance(author.get("email"), str) or not author.get("email", "").strip():
				_issue(issues, "warning", field + ".email", "An author email address is recommended.")
			if not isinstance(author.get("ORCID"), str) or not author.get("ORCID", "").strip():
				_issue(issues, "warning", field + ".ORCID", "An author ORCID is recommended.")
	for field in ("abstract", "tex"):
		value = data.get(field)
		if isinstance(value, list):
			for index, source in enumerate(value):
				_validate_source(issues, "{0}[{1}]".format(field, index), source, base_path, ("directory", "file", "text"))
	value = data.get("bib")
	if isinstance(value, list):
		for index, source in enumerate(value):
			_validate_source(issues, "bib[{0}]".format(index), source, base_path, ("directory", "file", "text"))
	value = data.get("figures")
	if isinstance(value, list):
		for index, source in enumerate(value):
			_validate_source(issues, "figures[{0}]".format(index), source, base_path, ("directory", "file", "base64"))
	targets = data.get("targets")
	if isinstance(targets, list):
		if not targets:
			_issue(issues, "warning", "targets", "No build targets are defined.")
		for index, target in enumerate(targets):
			field = "targets[{0}]".format(index)
			if not isinstance(target, dict):
				_issue(issues, "error", field, "A target entry must be a JSON object.")
				continue
			template = target.get("template")
			output = target.get("output")
			if not isinstance(template, dict):
				_issue(issues, "error", field + ".template", "template must be a JSON object.")
			else:
				for key in ("name", "category"):
					if not isinstance(template.get(key), str) or not template.get(key, "").strip():
						_issue(issues, "error", field + ".template." + key, key + " must not be empty.")
				if "engine" in template and not isinstance(template["engine"], str):
					_issue(issues, "error", field + ".template.engine", "engine must be a string.")
			if not isinstance(output, dict):
				_issue(issues, "error", field + ".output", "output must be a JSON object.")
			else:
				if not isinstance(output.get("path"), str) or not output.get("path", "").strip():
					_issue(issues, "error", field + ".output.path", "The output path must not be empty.")
				if output.get("type", "file") not in ("file", "directory"):
					_issue(issues, "error", field + ".output.type", "The output type must be file or directory.")
				if "encoding" in output:
					try:
						lookup(output["encoding"])
					except (LookupError, TypeError):
						_issue(issues, "error", field + ".output.encoding", "The output encoding name is invalid.")
				if "newline" in output and output["newline"] not in ("auto", "cr", "crlf", "lf", "macintosh", "unix", "windows"):
					_issue(issues, "error", field + ".output.newline", "The newline value is invalid.")
	return issues


class MetadataDocument:
	def __init__(self, file_path:Path | str | None = None) -> None:
		self.file_path:Path | None = None
		self.data = default_metadata()
		self.dirty = False
		if file_path is not None:
			self.load(file_path)

	@property
	def base_directory(self) -> Path:
		if self.file_path is None:
			return Path.cwd()
		return self.file_path.parent

	def load(self, file_path:Path | str) -> None:
		path = Path(file_path).expanduser().resolve()
		self.data = load_json(path)
		self.file_path = path
		self.dirty = False

	def set_field(self, key:str, value:Any) -> None:
		self.data[key] = deepcopy(value)
		self.dirty = True

	def set_list(self, key:str, values:list[Any]) -> None:
		self.data[key] = deepcopy(values)
		self.dirty = True

	def update_item(self, key:str, index:int, known_values:dict[str, Any]) -> None:
		item = deepcopy(self.data[key][index])
		if not isinstance(item, dict):
			item = {}
		merge_known(item, known_values)
		self.data[key][index] = item
		self.dirty = True

	def issues(self) -> list[ValidationIssue]:
		return validate_metadata(self.data, self.base_directory)

	def save(self, file_path:Path | str | None = None) -> None:
		if file_path is not None:
			self.file_path = Path(file_path).expanduser().resolve()
		if self.file_path is None:
			raise ValueError("No save path has been specified for metadata.json.")
		errors = [issue for issue in self.issues() if issue.severity == "error"]
		if errors:
			raise MetadataValidationError(errors)
		encoding = self.data.get("encoding", DEFAULT_ENCODING)
		lookup(encoding)
		target = self.file_path
		target.parent.mkdir(parents=True, exist_ok=True)
		temporary_path:Path | None = None
		try:
			with NamedTemporaryFile(
				mode="w",
				encoding=encoding,
				newline="\n",
				dir=target.parent,
				prefix="." + target.name + ".",
				suffix=".tmp",
				delete=False,
			) as temporary_file:
				temporary_file.write(dumps(self.data, ensure_ascii=False, indent="\t", sort_keys=True))
				temporary_file.write("\n")
				temporary_file.flush()
				fsync(temporary_file.fileno())
				temporary_path = Path(temporary_file.name)
			if target.exists():
				copy2(target, target.with_name(target.name + ".bak"))
			replace(temporary_path, target)
			temporary_path = None
			self.file_path = target
			self.dirty = False
		finally:
			if temporary_path is not None and temporary_path.exists():
				temporary_path.unlink()


class BuildRunner:
	def __init__(self, build_script:Path | str) -> None:
		self.build_script = Path(build_script).expanduser().resolve()
		self.events:Queue[tuple[str, Any]] = Queue()
		self.process:Popen[str] | None = None
		self.thread:Thread | None = None
		self._lock = Lock()

	@property
	def running(self) -> bool:
		with self._lock:
			return self.process is not None and self.process.poll() is None

	def command(self, metadata_path:Path | str) -> list[str]:
		return [executable, "-u", str(self.build_script), str(Path(metadata_path).expanduser().resolve())]

	def start(self, metadata_path:Path | str) -> None:
		with self._lock:
			if self.process is not None and self.process.poll() is None:
				raise RuntimeError("A build process is already running.")
			self.process = Popen(
				self.command(metadata_path),
				cwd=str(self.build_script.parent),
				stdout=PIPE,
				stderr=STDOUT,
				text=True,
				encoding="utf-8",
				errors="replace",
				bufsize=1,
			)
		self.thread = Thread(target=self._read_output, daemon=True)
		self.thread.start()

	def _read_output(self) -> None:
		with self._lock:
			process = self.process
		if process is None:
			return
		try:
			if process.stdout is not None:
				for line in process.stdout:
					self.events.put(("log", line))
			return_code = process.wait()
		finally:
			if process.stdout is not None:
				process.stdout.close()
		with self._lock:
			if self.process is process:
				self.process = None
		self.events.put(("done", return_code))

	def stop(self) -> bool:
		with self._lock:
			process = self.process
		if process is None or process.poll() is not None:
			return False
		process.terminate()
		try:
			process.wait(timeout=1)
		except TimeoutExpired:
			process.kill()
			process.wait(timeout=1)
		if self.thread is not None and self.thread is not current_thread():
			self.thread.join(timeout=2)
		return True


if tk is not None:
	class BaseDialog(tk.Toplevel):
		def __init__(self, parent:tk.Misc, title:str) -> None:
			super().__init__(parent)
			self.result:dict[str, Any] | None = None
			self.title(title)
			self.transient(parent.winfo_toplevel())
			self.resizable(True, True)
			self.protocol("WM_DELETE_WINDOW", self.destroy)
			self.columnconfigure(0, weight=1)
			self.rowconfigure(0, weight=1)
			self.body = ttk.Frame(self, padding=14)
			self.body.grid(row=0, column=0, sticky="nsew")
			self.body.columnconfigure(1, weight=1)
			buttons = ttk.Frame(self, padding=(14, 0, 14, 14))
			buttons.grid(row=1, column=0, sticky="ew")
			ttk.Button(buttons, text="Cancel", command=self.destroy).pack(side="right")
			ttk.Button(buttons, text="OK", command=self.accept).pack(side="right", padx=(0, 8))
			self.bind("<Escape>", lambda event:self.destroy())
			self.bind("<Control-Return>", lambda event:self.accept())

		def add_entry(self, row:int, label:str, value:Any = "") -> tk.StringVar:
			ttk.Label(self.body, text=label).grid(row=row, column=0, sticky="ne", padx=(0, 10), pady=5)
			variable = tk.StringVar(value="" if value is None else str(value))
			ttk.Entry(self.body, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=5)
			return variable

		def show(self) -> dict[str, Any] | None:
			self.wait_visibility()
			self.grab_set()
			self.focus_set()
			self.wait_window()
			return self.result

		def accept(self) -> None:
			raise NotImplementedError


	class AuthorDialog(BaseDialog):
		def __init__(self, parent:tk.Misc, value:Any = None) -> None:
			self.original = deepcopy(value) if isinstance(value, dict) else {}
			super().__init__(parent, "Edit Author")
			self.name = self.add_entry(0, "name", self.original.get("name", ""))
			self.email = self.add_entry(1, "email", self.original.get("email", ""))
			self.orcid = self.add_entry(2, "ORCID", self.original.get("ORCID", ""))
			ttk.Label(self.body, text="affiliations\n(one per line)").grid(row=3, column=0, sticky="ne", padx=(0, 10), pady=5)
			self.affiliations = tk.Text(self.body, height=6, width=48, wrap="word")
			self.affiliations.grid(row=3, column=1, sticky="nsew", pady=5)
			self.affiliations.insert("1.0", "\n".join(
				self.original.get("affiliations", []) if isinstance(self.original.get("affiliations"), list) else []
			))
			flags = ttk.Frame(self.body)
			flags.grid(row=4, column=1, sticky="w", pady=5)
			self.fa = tk.BooleanVar(value=self.original.get("FA") is True)
			self.ca = tk.BooleanVar(value=self.original.get("CA") is True)
			ttk.Checkbutton(flags, text="FA (co-first author)", variable=self.fa).pack(side="left")
			ttk.Checkbutton(flags, text="CA (corresponding author)", variable=self.ca).pack(side="left", padx=(14, 0))

		def accept(self) -> None:
			name = self.name.get().strip()
			if not name:
				messagebox.showerror("Author Details", "name must not be empty.", parent=self)
				return
			values = {
				"name":name,
				"email":self.email.get().strip(),
				"ORCID":self.orcid.get().strip(),
				"affiliations":[
					line.strip() for line in self.affiliations.get("1.0", "end-1c").splitlines() if line.strip()
				],
				"FA":self.fa.get(),
				"CA":self.ca.get(),
			}
			self.result = merge_known(self.original, values)
			self.destroy()


	class SourceDialog(BaseDialog):
		def __init__(
			self,
			parent:tk.Misc,
			value:Any,
			allowed_types:tuple[str, ...],
			base_directory:Path,
			title:str,
		) -> None:
			self.original = deepcopy(value) if isinstance(value, dict) else {}
			self.allowed_types = allowed_types
			self.base_directory = base_directory
			super().__init__(parent, title)
			ttk.Label(self.body, text="type").grid(row=0, column=0, sticky="e", padx=(0, 10), pady=5)
			self.source_type = tk.StringVar(value=self.original.get("type", allowed_types[0]))
			self.type_box = ttk.Combobox(
				self.body, textvariable=self.source_type, values=allowed_types, state="readonly",
			)
			self.type_box.grid(row=0, column=1, sticky="ew", pady=5)
			self.path = self.add_entry(1, "path", self.original.get("path", ""))
			path_buttons = ttk.Frame(self.body)
			path_buttons.grid(row=2, column=1, sticky="w")
			ttk.Button(path_buttons, text="Choose File", command=self._choose_file).pack(side="left")
			ttk.Button(path_buttons, text="Choose Directory", command=self._choose_directory).pack(side="left", padx=(8, 0))
			self.encoding = self.add_entry(3, "encoding", self.original.get("encoding", DEFAULT_ENCODING))
			self.filter = self.add_entry(4, "filter", self.original.get("filter", ""))
			self.reverse = tk.BooleanVar(value=self.original.get("reverse") is True)
			ttk.Checkbutton(self.body, text="reverse (reverse sort order)", variable=self.reverse).grid(
				row=5, column=1, sticky="w", pady=5,
			)
			self.name = self.add_entry(6, "name (Base64 file name)", self.original.get("name", ""))
			ttk.Label(self.body, text="text / base64").grid(row=7, column=0, sticky="ne", padx=(0, 10), pady=5)
			self.content = tk.Text(self.body, height=10, width=58, wrap="none")
			self.content.grid(row=7, column=1, sticky="nsew", pady=5)
			self.content.insert("1.0", self.original.get(
				"text", self.original.get("base64", ""),
			) if isinstance(self.original.get("text", self.original.get("base64", "")), str) else "")
			self.body.rowconfigure(7, weight=1)
			self.geometry("650x540")

		def _relative(self, selected:str) -> str:
			if not selected:
				return ""
			path = Path(selected)
			try:
				return str(path.relative_to(self.base_directory)).replace("\\", "/")
			except ValueError:
				return str(path)

		def _choose_file(self) -> None:
			selected = filedialog.askopenfilename(parent=self, initialdir=self.base_directory)
			if selected:
				self.path.set(self._relative(selected))

		def _choose_directory(self) -> None:
			selected = filedialog.askdirectory(parent=self, initialdir=self.base_directory, mustexist=True)
			if selected:
				self.path.set(self._relative(selected))

		def accept(self) -> None:
			source_type = self.source_type.get()
			values:dict[str, Any] = {"type":source_type}
			if source_type in ("file", "directory"):
				values["path"] = self.path.get().strip()
				values["encoding"] = self.encoding.get().strip() or DEFAULT_ENCODING
				if source_type == "directory":
					values["filter"] = self.filter.get()
					values["reverse"] = self.reverse.get()
			elif source_type == "text":
				values["text"] = self.content.get("1.0", "end-1c")
			elif source_type == "base64":
				values["name"] = self.name.get().strip()
				values["base64"] = self.content.get("1.0", "end-1c")
			self.result = merge_known(self.original, values)
			self.destroy()


	class TargetDialog(BaseDialog):
		def __init__(self, parent:tk.Misc, value:Any = None, base_directory:Path | None = None) -> None:
			self.original = deepcopy(value) if isinstance(value, dict) else {}
			self.base_directory = base_directory or Path.cwd()
			template = self.original.get("template") if isinstance(self.original.get("template"), dict) else {}
			output = self.original.get("output") if isinstance(self.original.get("output"), dict) else {}
			super().__init__(parent, "Edit Build Target")
			ttk.Label(self.body, text="Template").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 5))
			self.name = self.add_entry(1, "template.name", template.get("name", ""))
			ttk.Label(self.body, text="template.category").grid(row=2, column=0, sticky="e", padx=(0, 10), pady=5)
			self.category = tk.StringVar(value=template.get("category", "Publisher"))
			ttk.Combobox(
				self.body,
				textvariable=self.category,
				values=("Publisher", "Conferences", "Journals"),
			).grid(row=2, column=1, sticky="ew", pady=5)
			ttk.Label(self.body, text="template.engine").grid(row=3, column=0, sticky="e", padx=(0, 10), pady=5)
			self.engine = tk.StringVar(value=template.get("engine", "pdflatex"))
			ttk.Combobox(
				self.body,
				textvariable=self.engine,
				values=("pdflatex", "xelatex", "lualatex", "latex", "tex"),
			).grid(row=3, column=1, sticky="ew", pady=5)
			ttk.Separator(self.body).grid(row=4, column=0, columnspan=2, sticky="ew", pady=10)
			ttk.Label(self.body, text="Output").grid(row=5, column=0, columnspan=2, sticky="w", pady=(0, 5))
			self.output_path = self.add_entry(6, "output.path", output.get("path", ""))
			ttk.Label(self.body, text="output.type").grid(row=7, column=0, sticky="e", padx=(0, 10), pady=5)
			self.output_type = tk.StringVar(value=output.get("type", "file"))
			ttk.Combobox(
				self.body, textvariable=self.output_type, values=("file", "directory"), state="readonly",
			).grid(row=7, column=1, sticky="ew", pady=5)
			self.output_encoding = self.add_entry(8, "output.encoding", output.get("encoding", DEFAULT_ENCODING))
			ttk.Label(self.body, text="output.newline").grid(row=9, column=0, sticky="e", padx=(0, 10), pady=5)
			self.newline = tk.StringVar(value=output.get("newline", "auto"))
			ttk.Combobox(
				self.body,
				textvariable=self.newline,
				values=("auto", "lf", "crlf", "cr", "unix", "windows", "macintosh"),
				state="readonly",
			).grid(row=9, column=1, sticky="ew", pady=5)

		def accept(self) -> None:
			values = {
				"template":{
					"name":self.name.get().strip(),
					"category":self.category.get().strip(),
					"engine":self.engine.get().strip() or "pdflatex",
				},
				"output":{
					"path":self.output_path.get().strip(),
					"type":self.output_type.get(),
					"encoding":self.output_encoding.get().strip() or DEFAULT_ENCODING,
					"newline":self.newline.get(),
				},
			}
			self.result = merge_known(self.original, values)
			self.destroy()


	class GraphicalUserInterface:
		__DefaultPaddingValue = 5
		__DefaultBorderWidth = 2
		__DefaultFontFamily = "Times New Roman"
		__DefaultFontSize = 12
		def __init__(self, root:tk.Tk, file_path:Path | str | None = None) -> None:
			self.root = root
			self.document = MetadataDocument()
			self.build_runner = BuildRunner(Path(__file__).with_name("build.py"))
			self.preview_text:tk.Text | None = None
			self._diagnostic_job:str | None = None
			self._building = False
			self.__updating = False
			self.__paddingValue = GraphicalUserInterface.__DefaultPaddingValue
			self.__borderWidth = GraphicalUserInterface.__DefaultBorderWidth
			self.__fontFamily = GraphicalUserInterface.__DefaultFontFamily
			self.__font = tkfont.Font(
				family = self.__fontFamily, size = GraphicalUserInterface.__DefaultFontSize
			)
			self.__headingFont = tkfont.Font(family = self.__fontFamily, size = 16, weight = "bold")
			self.__listboxes:dict[str, tk.Listbox] = {}
			self.root.title("Generator")
			self.root.geometry("1180x820")
			self.root.minsize(900, 620)
			self.root.protocol("WM_DELETE_WINDOW", self.close)
			self._configure_style()
			self._build_shell()
			initial_path = Path(file_path).expanduser() if file_path else default_metadata_path()
			if initial_path.is_file():
				try:
					self.document.load(initial_path)
				except BaseException as error:
					messagebox.showerror("Open Failed", str(error), parent=self.root)
			elif file_path is not None:
				messagebox.showerror("Open Failed", "The file does not exist: {0}".format(initial_path), parent=self.root)
			else:
				self.document.file_path = initial_path.resolve()
			self.__refresh_all_fields()
			self.refresh_diagnostics()
			self.root.after(100, self._drain_build_events)

		def _configure_style(self) -> None:
			self.root.option_add("*Font", "{{{0}}} {1}".format(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))
			for font_name in (
				"TkDefaultFont", "TkTextFont", "TkFixedFont", "TkMenuFont", "TkHeadingFont",
				"TkCaptionFont", "TkSmallCaptionFont", "TkIconFont", "TkTooltipFont",
			):
				try:
					tkfont.nametofont(font_name).configure(family=DEFAULT_FONT_FAMILY)
				except tk.TclError:
					pass
			style = ttk.Style(self.root)
			try:
				style.theme_use("clam")
			except tk.TclError:
				pass
			style.configure("Custom.Treeview", font = self.__font, rowheight = 22)
			style.configure("Custom.Treeview.Heading", font = (self.__fontFamily, 12, "bold"))

		def _build_shell(self) -> None:
			self.root.columnconfigure(0, weight=1)
			self.root.rowconfigure(0, weight=1)
			container = tk.Frame(self.root)
			container.grid(row = 0, column = 0, sticky = "nsew")
			container.columnconfigure(0, weight=1)
			container.rowconfigure(0, weight=1)
			self.__canvas = tk.Canvas(container, highlightthickness=0)
			scrollbar = tk.Scrollbar(container, orient="vertical", command=self.__canvas.yview)
			self.__canvas.configure(yscrollcommand=scrollbar.set)
			self.__canvas.grid(row=0, column=0, sticky="nsew")
			scrollbar.grid(row=0, column=1, sticky="ns")
			self.__frame = tk.Frame(self.__canvas)
			self.__canvasWindow = self.__canvas.create_window((0, 0), window=self.__frame, anchor="nw")
			self.__frame.bind("<Configure>", self.__onFrameConfigured)
			self.__canvas.bind("<Configure>", self.__onCanvasConfigured)
			self.__canvas.bind_all("<MouseWheel>", self.__onMouseWheel)
			tk.Label(
				self.__frame, text = "Generator", font = self.__headingFont, fg = "red",
				anchor = "center", justify = "center"
			).pack(
				side = "top", fill = "x", expand = True,
				padx = self.__paddingValue, pady = self.__paddingValue
			)
			self.__buildPathEncodingFrame()
			self.__buildTitleFrame()
			self.__buildPackageAbstractKeywordFrame()
			self.__buildAuthorFrame()
			self.__buildContentFrame()
			self.__buildTargetFrame()
			self.__buildDiagnosticFrame()
			self.__buildPreviewFrame()
			self.status_variable = tk.StringVar(value="Ready")
			tk.Label(
				self.root, textvariable = self.status_variable, font = self.__font,
				relief = "sunken", anchor = "w"
			).grid(row = 1, column = 0, sticky = "ew")

		def __onFrameConfigured(self, event:Any = None) -> None:
			self.__canvas.configure(scrollregion=self.__canvas.bbox("all"))

		def __onCanvasConfigured(self, event:Any) -> None:
			self.__canvas.itemconfigure(self.__canvasWindow, width=event.width)

		def __onMouseWheel(self, event:Any) -> None:
			if event.delta:
				self.__canvas.yview_scroll(int(-event.delta / 120), "units")

		def __newSection(self, title:str) -> tk.Frame:
			section = tk.Frame(
				self.__frame, relief = "raised", borderwidth = self.__borderWidth
			)
			section.pack(
				side = "top", fill = "x", expand = True,
				padx = self.__paddingValue, pady = self.__paddingValue
			)
			tk.Label(
				section, text = title, font = self.__font, anchor = "w",
				justify = "left"
			).pack(side = "top", fill = "x", padx = self.__paddingValue, pady = self.__paddingValue)
			return section

		def __readonlyEntry(self, parent:tk.Misc, variable:tk.StringVar, width:int) -> tk.Entry:
			return tk.Entry(
				parent, textvariable = variable, font = self.__font,
				width = width, state = "readonly"
			)

		def __buildPathEncodingFrame(self) -> None:
			section = self.__newSection("Paths and Encoding")
			frame = tk.Frame(section)
			frame.pack(fill = "x", padx = self.__paddingValue, pady = self.__paddingValue)
			for column in (1, 4):
				frame.columnconfigure(column, weight=1)
			tk.Label(frame, text = "Executable path: ", font = self.__font).grid(row=0, column=0, sticky="e")
			executableVariable = tk.StringVar(value=executable)
			self.__readonlyEntry(frame, executableVariable, 38).grid(row=0, column=1, columnspan=2, sticky="ew")
			tk.Label(frame, text = "Script path: ", font = self.__font).grid(row=0, column=3, sticky="e")
			scriptVariable = tk.StringVar(value=str(Path(__file__).resolve()))
			self.__readonlyEntry(frame, scriptVariable, 38).grid(row=0, column=4, columnspan=3, sticky="ew")
			tk.Label(frame, text = "Metadata file path: ", font = self.__font).grid(row=1, column=0, sticky="e")
			self.path_variable = tk.StringVar()
			self.__readonlyEntry(frame, self.path_variable, 55).grid(row=1, column=1, columnspan=4, sticky="ew")
			self.open_button = tk.Button(frame, text = "Open", font = self.__font, command=self.open_file)
			self.open_button.grid(row=1, column=5, padx=(self.__paddingValue, 0))
			self.reload_button = tk.Button(frame, text = "Reload", font = self.__font, command=self.reload_file)
			self.reload_button.grid(row=1, column=6, padx=(self.__paddingValue, 0))
			tk.Label(frame, text = "Base directory: ", font = self.__font).grid(row=2, column=0, sticky="e")
			self.__baseDirectoryVariable = tk.StringVar()
			self.__readonlyEntry(frame, self.__baseDirectoryVariable, 40).grid(row=2, column=1, columnspan=2, sticky="ew")
			tk.Label(frame, text = "Encoding: ", font = self.__font).grid(row=2, column=3, sticky="e")
			self.__encodingVariable = tk.StringVar()
			tk.Entry(
				frame, textvariable = self.__encodingVariable, font = self.__font, width = 12
			).grid(row=2, column=4, sticky="w")
			self.__encodingVariable.trace_add("write", self.__onBasicChanged)
			buttonFrame = tk.Frame(frame)
			buttonFrame.grid(row=3, column=0, columnspan=7, sticky="e", pady=(self.__paddingValue, 0))
			self.save_button = tk.Button(
				buttonFrame, text = "Save metadata", font = self.__font, command=self.save
			)
			self.save_button.pack(side="left")
			self.build_button = tk.Button(
				buttonFrame, text = "Save and build", font = self.__font, command=self.save_and_build
			)
			self.build_button.pack(side="left", padx=(self.__paddingValue, 0))
			self.stop_button = tk.Button(
				buttonFrame, text = "Stop build", font = self.__font,
				command=self.stop_build, state="disabled"
			)
			self.stop_button.pack(side="left", padx=(self.__paddingValue, 0))

		def __buildTitleFrame(self) -> None:
			section = self.__newSection("Title")
			frame = tk.Frame(section)
			frame.pack(fill="x", padx=self.__paddingValue, pady=self.__paddingValue)
			frame.columnconfigure(1, weight=1)
			tk.Label(frame, text = "Title: ", font = self.__font).grid(row=0, column=0, sticky="e")
			self.__titleVariable = tk.StringVar()
			tk.Entry(
				frame, textvariable = self.__titleVariable, font = self.__font, width = 70
			).grid(row=0, column=1, sticky="ew")
			tk.Label(frame, text = "Title word count: ", font = self.__font).grid(row=0, column=2, sticky="e")
			self.__titleWordCountLabel = tk.Label(frame, text = "N/A", font = self.__font, fg = "red")
			self.__titleWordCountLabel.grid(row=0, column=3, sticky="w")
			tk.Label(frame, text = "Version: ", font = self.__font).grid(row=1, column=0, sticky="e")
			self.__versionVariable = tk.StringVar()
			tk.Entry(
				frame, textvariable = self.__versionVariable, font = self.__font, width = 18
			).grid(row=1, column=1, sticky="w", pady=(self.__paddingValue, 0))
			self.__titleVariable.trace_add("write", self.__onBasicChanged)
			self.__versionVariable.trace_add("write", self.__onBasicChanged)

		def __buildPackageAbstractKeywordFrame(self) -> None:
			section = self.__newSection("Packages, Abstract, and Keywords")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			for column in range(3):
				frame.columnconfigure(column, weight=1)
			self.__buildListGroup(frame, "packages", "Packages", 0)
			self.__buildListGroup(frame, "abstract", "Abstract sources", 1)
			self.__buildListGroup(frame, "keywords", "Keywords", 2)

		def __buildAuthorFrame(self) -> None:
			section = self.__newSection("Authors and Affiliations")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			frame.columnconfigure(0, weight=3)
			frame.columnconfigure(1, weight=1)
			self.__authorTreeview = ttk.Treeview(
				frame, columns=("Name", "Affiliations", "FA", "CA"),
				show="headings", height=7, style="Custom.Treeview"
			)
			for column, width in (("Name", 210), ("Affiliations", 300), ("FA", 70), ("CA", 70)):
				self.__authorTreeview.heading(column, text=column)
				self.__authorTreeview.column(column, width=width, anchor="center")
			self.__authorTreeview.grid(row=0, column=0, sticky="nsew")
			self.__authorTreeview.bind("<Double-Button-1>", lambda event:self.__editObject("authors"))
			affiliationFrame = tk.Frame(frame)
			affiliationFrame.grid(row=0, column=1, sticky="nsew", padx=(self.__paddingValue, 0))
			tk.Label(affiliationFrame, text = "Affiliations:", font = self.__font).pack(anchor="w")
			self.__affiliationListbox = tk.Listbox(
				affiliationFrame, font = self.__font, height = 7, exportselection = False
			)
			self.__affiliationListbox.pack(fill="both", expand=True)
			buttonFrame = tk.Frame(frame)
			buttonFrame.grid(row=1, column=0, columnspan=2, sticky="e", pady=(self.__paddingValue, 0))
			self.__buildObjectButtons(buttonFrame, "authors")

		def __buildContentFrame(self) -> None:
			section = self.__newSection("Content Sources")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			for column in range(3):
				frame.columnconfigure(column, weight=1)
			self.__buildListGroup(frame, "tex", "TeX", 0)
			self.__buildListGroup(frame, "bib", "Bibliography", 1)
			self.__buildListGroup(frame, "figures", "Figures", 2)

		def __buildTargetFrame(self) -> None:
			section = self.__newSection("Build Targets")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			frame.columnconfigure(0, weight=1)
			self.__listboxes["targets"] = tk.Listbox(
				frame, font = self.__font, height = 7, exportselection = False
			)
			self.__listboxes["targets"].grid(row=0, column=0, sticky="nsew")
			self.__listboxes["targets"].bind("<Double-Button-1>", lambda event:self.__editObject("targets"))
			buttonFrame = tk.Frame(frame)
			buttonFrame.grid(row=1, column=0, sticky="e", pady=(self.__paddingValue, 0))
			self.__buildObjectButtons(buttonFrame, "targets")

		def __buildDiagnosticFrame(self) -> None:
			section = self.__newSection("Validation and Build Log")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			frame.columnconfigure(0, weight=1)
			frame.columnconfigure(1, weight=2)
			tk.Label(frame, text = "Validation:", font = self.__font).grid(row=0, column=0, sticky="w")
			tk.Label(frame, text = "Build log:", font = self.__font).grid(row=0, column=1, sticky="w")
			self.issue_list = tk.Listbox(frame, font = self.__font, height = 10, activestyle="none")
			self.issue_list.grid(row=1, column=0, sticky="nsew", padx=(0, self.__paddingValue))
			self.log_text = tk.Text(
				frame, font = self.__font, height = 10, state = "disabled", wrap = "word"
			)
			self.log_text.grid(row=1, column=1, sticky="nsew")

		def __buildPreviewFrame(self) -> None:
			section = self.__newSection("JSON Preview")
			frame = tk.Frame(section)
			frame.pack(fill="both", expand=True, padx=self.__paddingValue, pady=self.__paddingValue)
			frame.columnconfigure(0, weight=1)
			self.preview_text = tk.Text(
				frame, wrap = "none", font = self.__font, height = 12, state = "disabled"
			)
			self.preview_text.grid(row=0, column=0, sticky="nsew")
			scrollbar = tk.Scrollbar(frame, orient="vertical", command=self.preview_text.yview)
			scrollbar.grid(row=0, column=1, sticky="ns")
			self.preview_text.configure(yscrollcommand=scrollbar.set)

		def __buildListGroup(self, parent:tk.Misc, field:str, title:str, column:int) -> None:
			frame = tk.Frame(parent, relief = "groove", borderwidth = 1)
			frame.grid(
				row=0, column=column, sticky="nsew",
				padx=(0 if column == 0 else self.__paddingValue, 0)
			)
			tk.Label(frame, text = title + ":", font = self.__font).pack(anchor="w")
			listbox = tk.Listbox(
				frame, font = self.__font, height = 7, exportselection = False
			)
			listbox.pack(fill="both", expand=True)
			self.__listboxes[field] = listbox
			if field in ("packages", "keywords"):
				listbox.bind("<Double-Button-1>", lambda event, value=field:self.__editString(value))
				buttonFrame = tk.Frame(frame)
				buttonFrame.pack(fill="x", pady=(self.__paddingValue, 0))
				for label, command in (
					("Add", lambda value=field:self.__addString(value)),
					("Edit", lambda value=field:self.__editString(value)),
					("Delete", lambda value=field:self.__deleteItem(value)),
					("Up", lambda value=field:self.__moveItem(value, -1)),
					("Down", lambda value=field:self.__moveItem(value, 1)),
				):
					tk.Button(buttonFrame, text=label, font=self.__font, command=command).pack(side="left")
			else:
				listbox.bind("<Double-Button-1>", lambda event, value=field:self.__editObject(value))
				buttonFrame = tk.Frame(frame)
				buttonFrame.pack(fill="x", pady=(self.__paddingValue, 0))
				self.__buildObjectButtons(buttonFrame, field)

		def __buildObjectButtons(self, parent:tk.Misc, field:str) -> None:
			for label, command in (
				("Add", lambda:self.__addObject(field)),
				("Edit", lambda:self.__editObject(field)),
				("Delete", lambda:self.__deleteItem(field)),
				("Up", lambda:self.__moveItem(field, -1)),
				("Down", lambda:self.__moveItem(field, 1)),
			):
				tk.Button(parent, text=label, font=self.__font, command=command).pack(side="left")

		def __onBasicChanged(self, *args:Any) -> None:
			if self.__updating:
				return
			title = self.__titleVariable.get()
			versionText = self.__versionVariable.get().strip()
			version:Any = int(versionText) if versionText.isdigit() else versionText
			encoding = self.__encodingVariable.get()
			changed = False
			for field, value in (("title", title), ("version", version), ("encoding", encoding)):
				if self.document.data.get(field) != value:
					self.document.set_field(field, value)
					changed = True
			self.__updateWordCount()
			if changed:
				self.schedule_refresh()

		def __updateWordCount(self) -> None:
			title = self.__titleVariable.get().strip()
			wordCount = len(title.split()) if title else 0
			color = "green" if 3 <= wordCount <= 15 else "orange"
			self.__titleWordCountLabel.config(text=str(wordCount), fg=color)

		def __listValues(self, field:str) -> list[Any]:
			values = self.document.data.get(field)
			return deepcopy(values) if isinstance(values, list) else []

		def __selectedIndex(self, field:str) -> int | None:
			if field == "authors":
				selection = self.__authorTreeview.selection()
				if not selection:
					return None
				try:
					return int(selection[0])
				except ValueError:
					return None
			listbox = self.__listboxes[field]
			selection = listbox.curselection()
			return selection[0] if selection else None

		def __setList(self, field:str, values:list[Any], selection:int | None = None) -> None:
			self.document.set_list(field, values)
			self.__refreshList(field, selection)
			self.schedule_refresh()

		def __addString(self, field:str) -> None:
			value = simpledialog.askstring(
				"Add " + field, "Value:", parent=self.root
			)
			if value is not None and value.strip():
				values = self.__listValues(field)
				values.append(value.strip())
				self.__setList(field, values, len(values) - 1)

		def __editString(self, field:str) -> None:
			index = self.__selectedIndex(field)
			if index is None:
				return
			values = self.__listValues(field)
			value = simpledialog.askstring(
				"Edit " + field, "Value:", initialvalue=values[index], parent=self.root
			)
			if value is not None and value.strip():
				values[index] = value.strip()
				self.__setList(field, values, index)

		def __showObjectDialog(self, field:str, value:Any) -> dict[str, Any] | None:
			if field == "authors":
				return AuthorDialog(self.root, value).show()
			if field == "targets":
				return TargetDialog(self.root, value, self.document.base_directory).show()
			allowedTypes = {
				"abstract":("directory", "file", "text"),
				"tex":("directory", "file", "text"),
				"bib":("directory", "file", "text"),
				"figures":("directory", "file", "base64"),
			}[field]
			return SourceDialog(
				self.root, value, allowedTypes, self.document.base_directory,
				"Edit {0} source".format(field)
			).show()

		def __addObject(self, field:str) -> None:
			value = self.__showObjectDialog(field, None)
			if value is not None:
				values = self.__listValues(field)
				values.append(value)
				self.__setList(field, values, len(values) - 1)

		def __editObject(self, field:str) -> None:
			index = self.__selectedIndex(field)
			if index is None:
				return
			values = self.__listValues(field)
			value = self.__showObjectDialog(field, values[index])
			if value is not None:
				values[index] = value
				self.__setList(field, values, index)

		def __deleteItem(self, field:str) -> None:
			index = self.__selectedIndex(field)
			if index is None:
				return
			values = self.__listValues(field)
			del values[index]
			self.__setList(field, values, min(index, len(values) - 1) if values else None)

		def __moveItem(self, field:str, offset:int) -> None:
			index = self.__selectedIndex(field)
			if index is None:
				return
			values = self.__listValues(field)
			target = index + offset
			if 0 <= target < len(values):
				values[index], values[target] = values[target], values[index]
				self.__setList(field, values, target)

		def __refreshList(self, field:str, selection:int | None = None) -> None:
			values = self.__listValues(field)
			if field == "authors":
				self.__authorTreeview.delete(*self.__authorTreeview.get_children())
				affiliations:list[str] = []
				for index, author in enumerate(values):
					if not isinstance(author, dict):
						continue
					authorAffiliations = author.get("affiliations")
					if not isinstance(authorAffiliations, list):
						authorAffiliations = []
					for affiliation in authorAffiliations:
						if isinstance(affiliation, str) and affiliation not in affiliations:
							affiliations.append(affiliation)
					self.__authorTreeview.insert(
						"", "end", iid=str(index), values=(
							author.get("name", ""),
							"; ".join(str(value) for value in authorAffiliations),
							"Yes" if author.get("FA") is True else "No",
							"Yes" if author.get("CA") is True else "No",
						)
					)
				self.__affiliationListbox.delete(0, "end")
				for affiliation in affiliations:
					self.__affiliationListbox.insert("end", affiliation)
				if selection is not None and str(selection) in self.__authorTreeview.get_children():
					self.__authorTreeview.selection_set(str(selection))
				return
			listbox = self.__listboxes[field]
			listbox.delete(0, "end")
			for value in values:
				if field in ("packages", "keywords"):
					summary = value
				elif field == "targets":
					summary = target_summary(value)
				else:
					summary = source_summary(value)
				listbox.insert("end", summary)
			if selection is not None and values:
				selection = max(0, min(selection, len(values) - 1))
				listbox.selection_set(selection)
				listbox.see(selection)

		def __refresh_all_fields(self) -> None:
			self.__updating = True
			try:
				self.path_variable.set(str(self.document.file_path or ""))
				self.__baseDirectoryVariable.set(str(self.document.base_directory))
				self.__encodingVariable.set(str(self.document.data.get("encoding", DEFAULT_ENCODING)))
				self.__titleVariable.set(str(self.document.data.get("title", "")))
				self.__versionVariable.set(str(self.document.data.get("version", "")))
			finally:
				self.__updating = False
			self.__updateWordCount()
			for field in ("packages", "abstract", "keywords", "authors", "tex", "bib", "figures", "targets"):
				self.__refreshList(field)
			self._refresh_preview()

		def reload_file(self) -> None:
			if self._building or self.document.file_path is None or not self._confirm_discard():
				return
			try:
				self.document.load(self.document.file_path)
				self.__refresh_all_fields()
				self.refresh_diagnostics()
			except BaseException as error:
				messagebox.showerror("Reload Failed", str(error), parent=self.root)

		def schedule_refresh(self) -> None:
			if self._diagnostic_job is not None:
				self.root.after_cancel(self._diagnostic_job)
			self._diagnostic_job = self.root.after(120, self.refresh_diagnostics)

		def refresh_diagnostics(self) -> None:
			self._diagnostic_job = None
			issues = self.document.issues()
			self.issue_list.delete(0, "end")
			for index, issue in enumerate(issues):
				prefix = "ERROR" if issue.severity == "error" else "WARNING"
				self.issue_list.insert("end", "[{0}] {1}\n  {2}".format(prefix, issue.field, issue.message))
				self.issue_list.itemconfig(index, foreground="#b42318" if issue.severity == "error" else "#946200")
			if not issues:
				self.issue_list.insert("end", "No issues found")
				self.issue_list.itemconfig(0, foreground="#28743e")
			errors = sum(issue.severity == "error" for issue in issues)
			warnings = sum(issue.severity == "warning" for issue in issues)
			dirty = "Unsaved" if self.document.dirty else "Saved"
			unknown = unknown_field_count(self.document.data)
			self.status_variable.set(
				"{0} · {1} error(s) · {2} warning(s) · {3} unknown field(s)".format(dirty, errors, warnings, unknown)
			)
			file_name = self.document.file_path.name if self.document.file_path else "metadata.json"
			self.root.title("{0}{1} — LaTeXBuilder Metadata Editor".format(
				"*" if self.document.dirty else "", file_name,
			))
			self.path_variable.set(str(self.document.file_path or "No file selected"))
			self.__baseDirectoryVariable.set(str(self.document.base_directory))
			self.__updateWordCount()
			self._refresh_preview()

		def _refresh_preview(self) -> None:
			if self.preview_text is None or not self.preview_text.winfo_exists():
				self.preview_text = None
				return
			content = dumps(self.document.data, ensure_ascii=False, indent="\t", sort_keys=True)
			self.preview_text.configure(state="normal")
			self.preview_text.delete("1.0", "end")
			self.preview_text.insert("1.0", content)
			self.preview_text.configure(state="disabled")

		def _confirm_discard(self) -> bool:
			if not self.document.dirty:
				return True
			answer = messagebox.askyesnocancel(
				"Unsaved Changes",
				"The current file has unsaved changes.\n\nChoose Yes to save first, or No to discard the changes.",
				parent=self.root,
			)
			if answer is None:
				return False
			if answer is True:
				return self.save()
			return True

		def open_file(self) -> None:
			if self._building or not self._confirm_discard():
				return
			selected = filedialog.askopenfilename(
				parent=self.root,
				title="Open metadata.json",
				filetypes=(("JSON Files", "*.json"), ("All Files", "*.*")),
				initialdir=self.document.base_directory,
			)
			if not selected:
				return
			try:
				self.document.load(selected)
				self.__refresh_all_fields()
				self.refresh_diagnostics()
			except BaseException as error:
				messagebox.showerror("Open Failed", str(error), parent=self.root)

		def save(self) -> bool:
			if self._building:
				return False
			if self.document.file_path is None:
				selected = filedialog.asksaveasfilename(
					parent=self.root,
					title="Save metadata.json",
					defaultextension=".json",
					filetypes=(("JSON Files", "*.json"),),
				)
				if not selected:
					return False
				self.document.file_path = Path(selected).resolve()
			issues = self.document.issues()
			errors = [issue for issue in issues if issue.severity == "error"]
			if errors:
				message = "\n".join("• {0}: {1}".format(issue.field, issue.message) for issue in errors[:8])
				if len(errors) > 8:
					message += "\n• {0} additional error(s)".format(len(errors) - 8)
				messagebox.showerror("Unable to Save", "Fix the following blocking errors first:\n\n" + message, parent=self.root)
				self.refresh_diagnostics()
				return False
			try:
				self.document.save()
				self.refresh_diagnostics()
				return True
			except BaseException as error:
				messagebox.showerror("Save Failed", str(error), parent=self.root)
				return False

		def save_and_build(self) -> None:
			if not self.save() or self.document.file_path is None:
				return
			if not self.build_runner.build_script.is_file():
				messagebox.showerror("Build Failed", "build.py was not found: {0}".format(self.build_runner.build_script), parent=self.root)
				return
			self._set_building(True)
			self._clear_log()
			self._append_log("$ {0}\n\n".format(" ".join(self.build_runner.command(self.document.file_path))))
			try:
				self.build_runner.start(self.document.file_path)
			except BaseException as error:
				self._set_building(False)
				messagebox.showerror("Build Failed", str(error), parent=self.root)

		def stop_build(self) -> None:
			if not self._building:
				return
			self.stop_button.configure(state="disabled")
			self.status_variable.set("Stopping build…")
			Thread(target=self.build_runner.stop, daemon=True).start()

		def _set_building(self, building:bool) -> None:
			self._building = building
			state = "disabled" if building else "normal"
			for button in (self.open_button, self.reload_button, self.save_button, self.build_button):
				button.configure(state=state)
			self.stop_button.configure(state="normal" if building else "disabled")
			if building:
				self.status_variable.set("Building…")
			else:
				self.refresh_diagnostics()

		def _clear_log(self) -> None:
			self.log_text.configure(state="normal")
			self.log_text.delete("1.0", "end")
			self.log_text.configure(state="disabled")

		def _append_log(self, text:str) -> None:
			self.log_text.configure(state="normal")
			self.log_text.insert("end", text)
			self.log_text.see("end")
			self.log_text.configure(state="disabled")

		def _drain_build_events(self) -> None:
			try:
				while True:
					event, value = self.build_runner.events.get_nowait()
					if event == "log":
						self._append_log(value)
					elif event == "done":
						self._append_log("\nBuild process exit code: {0}\n".format(value))
						self._set_building(False)
						if value != EXIT_SUCCESS:
							messagebox.showwarning("Build Unsuccessful", "The build process exited with code {0}. Review the log on the right.".format(value), parent=self.root)
			except Empty:
				pass
			if self.root.winfo_exists():
				self.root.after(100, self._drain_build_events)

		def close(self) -> None:
			if not self._confirm_discard():
				return
			if self._building:
				if not messagebox.askyesno("Build in Progress", "A build is still running. Stop it and exit?", parent=self.root):
					return
				self.build_runner.stop()
			self.root.destroy()

	MetadataEditorApp = GraphicalUserInterface


def default_metadata_path() -> Path:
	return Path(__file__).resolve().with_name("metadata.json")


def main(arguments:list[str] | None = None) -> int:
	arguments = argv[1:] if arguments is None else arguments
	if tk is None:
		print("Unable to start the visual editor because Tkinter is not installed for this Python interpreter ({0}).".format(TKINTER_IMPORT_ERROR))
		return EXIT_FAILURE
	root = tk.Tk()
	GraphicalUserInterface(root, arguments[0] if arguments else None)
	root.mainloop()
	return EXIT_SUCCESS


if "__main__" == __name__:
	raise SystemExit(main())
