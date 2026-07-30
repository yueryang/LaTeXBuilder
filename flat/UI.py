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
	from tkinter import filedialog, font as tkfont, messagebox, ttk
	TKINTER_IMPORT_ERROR:BaseException | None = None
except ImportError as error:
	tk = None
	filedialog = None
	tkfont = None
	messagebox = None
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
				temporary_file.write(dumps(self.data, ensure_ascii = True, indent = "\t", sort_keys = True))
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


	class StringListEditor(ttk.Frame):
		def __init__(self, parent:tk.Misc, values:list[Any], on_commit, height:int = 12) -> None:
			super().__init__(parent)
			self.values = [value if isinstance(value, str) else str(value) for value in values]
			self.on_commit = on_commit
			self.columnconfigure(0, weight=1)
			self.rowconfigure(0, weight=1)
			self.listbox = tk.Listbox(self, height=height, activestyle="dotbox", exportselection=False)
			self.listbox.grid(row=0, column=0, columnspan=5, sticky="nsew")
			scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.listbox.yview)
			scrollbar.grid(row=0, column=5, sticky="ns")
			self.listbox.configure(yscrollcommand=scrollbar.set)
			self.entry = ttk.Entry(self)
			self.entry.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 6))
			for column, (text, command) in enumerate((
				("Add", self.add), ("Update", self.edit), ("Delete", self.delete), ("Move Up", lambda:self.move(-1)), ("Move Down", lambda:self.move(1)),
			)):
				ttk.Button(self, text=text, command=command).grid(row=2, column=column, sticky="ew", padx=(0, 6))
			self.listbox.bind("<<ListboxSelect>>", self._select)
			self.listbox.bind("<Double-Button-1>", lambda event:self.edit())
			self.entry.bind("<Return>", lambda event:self.add())
			self.refresh()

		def refresh(self, selection:int | None = None) -> None:
			self.listbox.delete(0, "end")
			for value in self.values:
				self.listbox.insert("end", value)
			if selection is not None and self.values:
				selection = max(0, min(selection, len(self.values) - 1))
				self.listbox.selection_set(selection)
				self.listbox.see(selection)

		def _selected(self) -> int | None:
			selection = self.listbox.curselection()
			return selection[0] if selection else None

		def _select(self, event:Any = None) -> None:
			index = self._selected()
			if index is not None:
				self.entry.delete(0, "end")
				self.entry.insert(0, self.values[index])

		def add(self) -> None:
			value = self.entry.get().strip()
			if value:
				self.values.append(value)
				self.entry.delete(0, "end")
				self.refresh(len(self.values) - 1)
				self.on_commit(deepcopy(self.values))

		def edit(self) -> None:
			index = self._selected()
			value = self.entry.get().strip()
			if index is not None and value:
				self.values[index] = value
				self.refresh(index)
				self.on_commit(deepcopy(self.values))

		def delete(self) -> None:
			index = self._selected()
			if index is not None:
				del self.values[index]
				self.entry.delete(0, "end")
				self.refresh(index)
				self.on_commit(deepcopy(self.values))

		def move(self, offset:int) -> None:
			index = self._selected()
			if index is None:
				return
			target = index + offset
			if 0 <= target < len(self.values):
				self.values[index], self.values[target] = self.values[target], self.values[index]
				self.refresh(target)
				self.on_commit(deepcopy(self.values))


	class ObjectListEditor(ttk.Frame):
		def __init__(self, parent:tk.Misc, values:list[Any], summary, edit_dialog, on_commit) -> None:
			super().__init__(parent)
			self.values = deepcopy(values)
			self.summary = summary
			self.edit_dialog = edit_dialog
			self.on_commit = on_commit
			self.columnconfigure(0, weight=1)
			self.rowconfigure(0, weight=1)
			self.listbox = tk.Listbox(self, height=16, activestyle="dotbox", exportselection=False)
			self.listbox.grid(row=0, column=0, columnspan=5, sticky="nsew")
			scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.listbox.yview)
			scrollbar.grid(row=0, column=5, sticky="ns")
			self.listbox.configure(yscrollcommand=scrollbar.set)
			for column, (text, command) in enumerate((
				("Add", self.add), ("Edit", self.edit), ("Delete", self.delete), ("Move Up", lambda:self.move(-1)), ("Move Down", lambda:self.move(1)),
			)):
				ttk.Button(self, text=text, command=command).grid(row=1, column=column, sticky="ew", padx=(0, 6), pady=(8, 0))
			self.listbox.bind("<Double-Button-1>", lambda event:self.edit())
			self.refresh()

		def refresh(self, selection:int | None = None) -> None:
			self.listbox.delete(0, "end")
			for value in self.values:
				self.listbox.insert("end", self.summary(value))
			if selection is not None and self.values:
				selection = max(0, min(selection, len(self.values) - 1))
				self.listbox.selection_set(selection)
				self.listbox.see(selection)

		def _selected(self) -> int | None:
			selection = self.listbox.curselection()
			return selection[0] if selection else None

		def add(self) -> None:
			value = self.edit_dialog(None)
			if value is not None:
				self.values.append(value)
				self.refresh(len(self.values) - 1)
				self.on_commit(deepcopy(self.values))

		def edit(self) -> None:
			index = self._selected()
			if index is None:
				return
			value = self.edit_dialog(self.values[index])
			if value is not None:
				self.values[index] = value
				self.refresh(index)
				self.on_commit(deepcopy(self.values))

		def delete(self) -> None:
			index = self._selected()
			if index is not None:
				del self.values[index]
				self.refresh(index)
				self.on_commit(deepcopy(self.values))

		def move(self, offset:int) -> None:
			index = self._selected()
			if index is None:
				return
			target = index + offset
			if 0 <= target < len(self.values):
				self.values[index], self.values[target] = self.values[target], self.values[index]
				self.refresh(target)
				self.on_commit(deepcopy(self.values))


	class MetadataEditorApp:
		NAVIGATION = (
			("basic", "General"),
			("authors", "Authors and Affiliations"),
			("abstract", "Abstract and Keywords"),
			("packages", "LaTeX Packages"),
			("tex", "Manuscript Sources"),
			("bib", "Bibliography"),
			("figures", "Figures"),
			("targets", "Build Targets"),
			("preview", "JSON Preview"),
		)

		def __init__(self, root:tk.Tk, file_path:Path | str | None = None) -> None:
			self.root = root
			self.document = MetadataDocument()
			self.build_runner = BuildRunner(Path(__file__).with_name("build.py"))
			self.current_page = "basic"
			self.nav_buttons:dict[str, ttk.Button] = {}
			self.preview_text:tk.Text | None = None
			self._page_variables:list[tk.Variable] = []
			self._diagnostic_job:str | None = None
			self._building = False
			self.root.title("LaTeXBuilder Metadata Editor")
			self.root.geometry("1240x780")
			self.root.minsize(980, 620)
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
			self.show_page("basic")
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
			style.configure("Toolbar.TFrame", background="#263547")
			style.configure("Toolbar.TLabel", background="#263547", foreground="#dce6ef")
			style.configure("Sidebar.TFrame", background="#f1f4f7")
			style.configure("Sidebar.TButton", anchor="w", padding=(12, 9))
			style.configure("Active.Sidebar.TButton", anchor="w", padding=(12, 9), background="#dbe8f5")
			style.configure("Title.TLabel", font=(DEFAULT_FONT_FAMILY, 15, "bold"))

		def _build_shell(self) -> None:
			self.root.columnconfigure(0, weight=1)
			self.root.rowconfigure(1, weight=1)
			toolbar = ttk.Frame(self.root, style="Toolbar.TFrame", padding=(12, 9))
			toolbar.grid(row=0, column=0, sticky="ew")
			self.open_button = ttk.Button(toolbar, text="Open", command=self.open_file)
			self.open_button.pack(side="left")
			self.save_button = ttk.Button(toolbar, text="Save", command=self.save)
			self.save_button.pack(side="left", padx=(7, 0))
			self.build_button = ttk.Button(toolbar, text="Save and Build", command=self.save_and_build)
			self.build_button.pack(side="left", padx=(7, 0))
			self.stop_button = ttk.Button(toolbar, text="Stop Build", command=self.stop_build, state="disabled")
			self.stop_button.pack(side="left", padx=(7, 0))
			self.path_variable = tk.StringVar()
			ttk.Label(toolbar, textvariable=self.path_variable, style="Toolbar.TLabel").pack(
				side="right", padx=(20, 0),
			)
			body = ttk.Panedwindow(self.root, orient="horizontal")
			body.grid(row=1, column=0, sticky="nsew")
			sidebar = ttk.Frame(body, style="Sidebar.TFrame", padding=8, width=190)
			for page, label in self.NAVIGATION:
				button = ttk.Button(
					sidebar, text=label, style="Sidebar.TButton", command=lambda value=page:self.show_page(value),
				)
				button.pack(fill="x", pady=1)
				self.nav_buttons[page] = button
			body.add(sidebar, weight=0)
			self.editor = ttk.Frame(body, padding=20)
			self.editor.columnconfigure(0, weight=1)
			self.editor.rowconfigure(1, weight=1)
			body.add(self.editor, weight=4)
			inspector = ttk.Frame(body, padding=10, width=300)
			inspector.columnconfigure(0, weight=1)
			inspector.rowconfigure(1, weight=1)
			inspector.rowconfigure(3, weight=2)
			ttk.Label(inspector, text="Validation", style="Title.TLabel").grid(row=0, column=0, sticky="w")
			self.issue_list = tk.Listbox(inspector, height=9, activestyle="none")
			self.issue_list.grid(row=1, column=0, sticky="nsew", pady=(7, 12))
			ttk.Label(inspector, text="Build Log", style="Title.TLabel").grid(row=2, column=0, sticky="w")
			self.log_text = tk.Text(
				inspector, height=16, width=38, state="disabled", wrap="word",
				background="#1f2933", foreground="#d6e0ea", insertbackground="#ffffff",
			)
			self.log_text.grid(row=3, column=0, sticky="nsew", pady=(7, 0))
			body.add(inspector, weight=2)
			self.status_variable = tk.StringVar(value="Ready")
			ttk.Label(self.root, textvariable=self.status_variable, padding=(10, 6), relief="sunken").grid(
				row=2, column=0, sticky="ew",
			)

		def _clear_editor(self, title:str, subtitle:str = "") -> ttk.Frame:
			for child in self.editor.winfo_children():
				child.destroy()
			self._page_variables = []
			header = ttk.Frame(self.editor)
			header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
			ttk.Label(header, text=title, style="Title.TLabel").pack(anchor="w")
			if subtitle:
				ttk.Label(header, text=subtitle, foreground="#647587").pack(anchor="w", pady=(3, 0))
			content = ttk.Frame(self.editor)
			content.grid(row=1, column=0, sticky="nsew")
			content.columnconfigure(0, weight=1)
			content.rowconfigure(0, weight=1)
			return content

		def show_page(self, page:str) -> None:
			self.current_page = page
			for key, button in self.nav_buttons.items():
				button.configure(style="Active.Sidebar.TButton" if key == page else "Sidebar.TButton")
			builders = {
				"basic":self._page_basic,
				"authors":self._page_authors,
				"abstract":self._page_abstract,
				"packages":self._page_packages,
				"tex":lambda:self._page_sources("tex", "Manuscript Sources", ("directory", "file", "text")),
				"bib":lambda:self._page_sources("bib", "Bibliography", ("directory", "file", "text")),
				"figures":lambda:self._page_sources("figures", "Figures", ("directory", "file", "base64")),
				"targets":self._page_targets,
				"preview":self._page_preview,
			}
			builders[page]()

		def _page_basic(self) -> None:
			content = self._clear_editor("General", "Edit the manuscript title, metadata version, and file encoding.")
			form = ttk.Frame(content)
			form.grid(row=0, column=0, sticky="new")
			form.columnconfigure(1, weight=1)
			values = (
				("title", "Manuscript Title", self.document.data.get("title", "")),
				("version", "Metadata Version", self.document.data.get("version", "")),
				("encoding", "File Encoding", self.document.data.get("encoding", DEFAULT_ENCODING)),
			)
			for row, (key, label, value) in enumerate(values):
				ttk.Label(form, text=label).grid(row=row, column=0, sticky="e", padx=(0, 12), pady=8)
				variable = tk.StringVar(value=str(value))
				self._page_variables.append(variable)
				ttk.Entry(form, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=8)
				variable.trace_add("write", lambda *args, field=key, source=variable:self._basic_changed(field, source.get()))
			path_box = ttk.LabelFrame(form, text="Current File", padding=12)
			path_box.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(18, 0))
			ttk.Label(path_box, text=str(self.document.file_path or "Not specified")).pack(anchor="w")
			ttk.Label(path_box, text="All relative paths are resolved from this file's directory.", foreground="#647587").pack(
				anchor="w", pady=(6, 0),
			)

		def _basic_changed(self, field:str, value:str) -> None:
			if field == "version":
				parsed:Any = int(value) if value.strip().isdigit() else value
			else:
				parsed = value
			if self.document.data.get(field) != parsed:
				self.document.set_field(field, parsed)
				self.schedule_refresh()

		def _page_authors(self) -> None:
			content = self._clear_editor("Authors and Affiliations", "Double-click an item to edit it. Unknown author fields are preserved.")
			editor = ObjectListEditor(
				content,
				self.document.data.get("authors", []) if isinstance(self.document.data.get("authors"), list) else [],
				author_summary,
				lambda value:AuthorDialog(self.root, value).show(),
				lambda values:self._set_list("authors", values),
			)
			editor.grid(row=0, column=0, sticky="nsew")

		def _page_abstract(self) -> None:
			content = self._clear_editor("Abstract and Keywords", "Abstracts may come from files, directories, or direct text. Keywords can be reordered.")
			panes = ttk.Panedwindow(content, orient="vertical")
			panes.grid(row=0, column=0, sticky="nsew")
			abstract_frame = ttk.LabelFrame(panes, text="abstract", padding=10)
			abstract_frame.columnconfigure(0, weight=1)
			abstract_frame.rowconfigure(0, weight=1)
			abstract_editor = ObjectListEditor(
				abstract_frame,
				self.document.data.get("abstract", []) if isinstance(self.document.data.get("abstract"), list) else [],
				source_summary,
				lambda value:SourceDialog(
					self.root, value, ("directory", "file", "text"), self.document.base_directory, "Edit Abstract Source",
				).show(),
				lambda values:self._set_list("abstract", values),
			)
			abstract_editor.grid(row=0, column=0, sticky="nsew")
			panes.add(abstract_frame, weight=2)
			keyword_frame = ttk.LabelFrame(panes, text="keywords", padding=10)
			keyword_frame.columnconfigure(0, weight=1)
			keyword_frame.rowconfigure(0, weight=1)
			StringListEditor(
				keyword_frame,
				self.document.data.get("keywords", []) if isinstance(self.document.data.get("keywords"), list) else [],
				lambda values:self._set_list("keywords", values),
				height=6,
			).grid(row=0, column=0, sticky="nsew")
			panes.add(keyword_frame, weight=1)

		def _page_packages(self) -> None:
			content = self._clear_editor("LaTeX Packages", "Each item contains one complete \\usepackage command.")
			StringListEditor(
				content,
				self.document.data.get("packages", []) if isinstance(self.document.data.get("packages"), list) else [],
				lambda values:self._set_list("packages", values),
			).grid(row=0, column=0, sticky="nsew")

		def _page_sources(self, field:str, title:str, allowed_types:tuple[str, ...]) -> None:
			content = self._clear_editor(title, "Source paths are relative to the directory containing metadata.json.")
			ObjectListEditor(
				content,
				self.document.data.get(field, []) if isinstance(self.document.data.get(field), list) else [],
				source_summary,
				lambda value:SourceDialog(
					self.root, value, allowed_types, self.document.base_directory, "Edit " + field + " Source",
				).show(),
				lambda values:self._set_list(field, values),
			).grid(row=0, column=0, sticky="nsew")

		def _page_targets(self) -> None:
			content = self._clear_editor("Build Targets", "Set the template identifier, LaTeX engine, and output location.")
			ObjectListEditor(
				content,
				self.document.data.get("targets", []) if isinstance(self.document.data.get("targets"), list) else [],
				target_summary,
				lambda value:TargetDialog(self.root, value, self.document.base_directory).show(),
				lambda values:self._set_list("targets", values),
			).grid(row=0, column=0, sticky="nsew")

		def _page_preview(self) -> None:
			content = self._clear_editor("JSON Preview", "This read-only preview includes all unknown and extension fields.")
			self.preview_text = tk.Text(content, wrap="none", font=(DEFAULT_FONT_FAMILY, DEFAULT_FONT_SIZE))
			self.preview_text.grid(row=0, column=0, sticky="nsew")
			vertical = ttk.Scrollbar(content, orient="vertical", command=self.preview_text.yview)
			vertical.grid(row=0, column=1, sticky="ns")
			horizontal = ttk.Scrollbar(content, orient="horizontal", command=self.preview_text.xview)
			horizontal.grid(row=1, column=0, sticky="ew")
			self.preview_text.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
			self._refresh_preview()

		def _set_list(self, field:str, values:list[Any]) -> None:
			self.document.set_list(field, values)
			self.schedule_refresh()

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
				self.show_page("basic")
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
			for button in (self.open_button, self.save_button, self.build_button):
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


def default_metadata_path() -> Path:
	return Path(__file__).resolve().with_name("metadata.json")


def main(arguments:list[str] | None = None) -> int:
	arguments = argv[1:] if arguments is None else arguments
	if tk is None:
		print("Unable to start the visual editor because Tkinter is not installed for this Python interpreter ({0}).".format(TKINTER_IMPORT_ERROR))
		return EXIT_FAILURE
	root = tk.Tk()
	MetadataEditorApp(root, arguments[0] if arguments else None)
	root.mainloop()
	return EXIT_SUCCESS


if "__main__" == __name__:
	raise SystemExit(main())
