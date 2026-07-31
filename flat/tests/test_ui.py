import json
import queue
import re
import sys
import tempfile
import time
import unittest
from pathlib import Path


FLAT_DIRECTORY = Path(__file__).resolve().parents[1]
if str(FLAT_DIRECTORY) not in sys.path:
	sys.path.insert(0, str(FLAT_DIRECTORY))

from UI import (
	BuildRunner,
	DEFAULT_FONT_FAMILY,
	MetadataDocument,
	author_summary,
	merge_known,
	source_summary,
	target_summary,
	unknown_field_count,
	validate_metadata,
)


def valid_metadata(base_directory):
	source_directory = base_directory / "sources"
	source_directory.mkdir(exist_ok=True)
	(source_directory / "abstract.tex").write_text("Abstract", encoding="utf-8")
	(source_directory / "main.tex").write_text("Content", encoding="utf-8")
	return {
		"abstract": [{"encoding":"utf-8", "path":"sources/abstract.tex", "type":"file"}],
		"authors": [{
			"CA":True,
			"FA":True,
			"ORCID":"0000-0000-0000-0001",
			"affiliations":["Example University"],
			"email":"author@example.com",
			"name":"Example Author",
		}],
		"bib": [],
		"encoding":"utf-8",
		"figures": [],
		"keywords":["LaTeX"],
		"packages":["\\usepackage{amsmath}"],
		"targets": [{
			"output":{"encoding":"utf-8", "path":"targets/Example/main.tex", "type":"file"},
			"template":{"category":"Publisher", "name":"Elsevier"},
		}],
		"tex": [{"encoding":"utf-8", "path":"sources/main.tex", "type":"file"}],
		"title":"A Useful Example Title",
		"version":20260730,
	}


class MetadataDocumentTests(unittest.TestCase):
	def test_load_update_and_save_preserve_unknown_fields(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			file_path = base_directory / "metadata.json"
			data = valid_metadata(base_directory)
			data["customTop"] = {"enabled":True}
			data["authors"][0]["customAuthor"] = "keep-me"
			file_path.write_text(json.dumps(data), encoding="utf-8")

			document = MetadataDocument(file_path)
			document.update_item("authors", 0, {"name":"Changed Author"})
			document.set_field("title", "A Changed Example Title")
			document.save()

			saved = json.loads(file_path.read_text(encoding="utf-8"))
			self.assertEqual(saved["customTop"], {"enabled":True})
			self.assertEqual(saved["authors"][0]["customAuthor"], "keep-me")
			self.assertEqual(saved["authors"][0]["name"], "Changed Author")
			self.assertEqual(saved["title"], "A Changed Example Title")

	def test_merge_known_recursively_preserves_nested_unknown_fields(self):
		original = {
			"template":{"name":"Elsevier", "category":"Publisher", "custom":"keep"},
			"output":{"path":"old.tex", "customOutput":7},
		}
		merge_known(original, {
			"template":{"name":"Nature"},
			"output":{"path":"new.tex"},
		})
		self.assertEqual(original["template"]["custom"], "keep")
		self.assertEqual(original["output"]["customOutput"], 7)
		self.assertEqual(original["template"]["name"], "Nature")
		self.assertEqual(original["output"]["path"], "new.tex")

	def test_second_save_creates_one_backup_of_previous_file(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			file_path = base_directory / "metadata.json"
			document = MetadataDocument()
			document.file_path = file_path
			document.data = valid_metadata(base_directory)
			document.save()
			document.set_field("title", "A Second Valid Example Title")
			document.save()

			backup_path = file_path.with_name(file_path.name + ".bak")
			self.assertTrue(backup_path.is_file())
			backup = json.loads(backup_path.read_text(encoding="utf-8"))
			current = json.loads(file_path.read_text(encoding="utf-8"))
			self.assertEqual(backup["title"], "A Useful Example Title")
			self.assertEqual(current["title"], "A Second Valid Example Title")

	def test_utf8_bom_file_loads(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			file_path = base_directory / "metadata.json"
			data = valid_metadata(base_directory)
			file_path.write_text(json.dumps(data), encoding="utf-8-sig")
			document = MetadataDocument(file_path)
			self.assertEqual(document.data["title"], "A Useful Example Title")


class ValidationTests(unittest.TestCase):
	def test_invalid_encoding_and_missing_source_are_errors(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			data = valid_metadata(base_directory)
			data["encoding"] = "not-an-encoding"
			data["tex"][0]["path"] = "sources/missing.tex"
			issues = validate_metadata(data, base_directory)
			error_fields = {issue.field for issue in issues if issue.severity == "error"}
			self.assertIn("encoding", error_fields)
			self.assertIn("tex[0].path", error_fields)

	def test_short_title_and_missing_optional_author_details_are_warnings(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			data = valid_metadata(base_directory)
			data["title"] = "Short"
			data["authors"][0].pop("email")
			data["authors"][0].pop("ORCID")
			issues = validate_metadata(data, base_directory)
			warning_fields = {issue.field for issue in issues if issue.severity == "warning"}
			self.assertIn("title", warning_fields)
			self.assertIn("authors[0].email", warning_fields)
			self.assertIn("authors[0].ORCID", warning_fields)

	def test_malformed_target_is_an_error(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			data = valid_metadata(base_directory)
			data["targets"][0]["template"].pop("category")
			data["targets"][0]["output"]["type"] = "socket"
			issues = validate_metadata(data, base_directory)
			error_fields = {issue.field for issue in issues if issue.severity == "error"}
			self.assertIn("targets[0].template.category", error_fields)
			self.assertIn("targets[0].output.type", error_fields)

	def test_relative_source_paths_use_metadata_directory(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			data = valid_metadata(base_directory)
			issues = validate_metadata(data, base_directory)
			source_errors = [
				issue for issue in issues
				if issue.severity == "error" and issue.field.startswith(("abstract", "tex"))
			]
			self.assertEqual(source_errors, [])


class BuildRunnerTests(unittest.TestCase):
	def test_streams_log_lines_and_completion_event(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			metadata_path = base_directory / "metadata.json"
			metadata_path.write_text("{}", encoding="utf-8")
			build_script = base_directory / "build.py"
			build_script.write_text(
				"import pathlib, sys\n"
				"print(pathlib.Path(sys.argv[1]).is_absolute(), flush=True)\n"
				"print('second line', flush=True)\n",
				encoding="utf-8",
			)
			runner = BuildRunner(build_script)
			runner.start(metadata_path)

			events = []
			deadline = time.monotonic() + 5
			while time.monotonic() < deadline:
				try:
					event = runner.events.get(timeout=0.2)
				except queue.Empty:
					continue
				events.append(event)
				if event[0] == "done":
					break

			self.assertIn(("log", "True\n"), events)
			self.assertIn(("log", "second line\n"), events)
			self.assertIn(("done", 0), events)
			self.assertFalse(runner.running)

	def test_start_rejects_a_second_running_process(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			metadata_path = base_directory / "metadata.json"
			metadata_path.write_text("{}", encoding="utf-8")
			build_script = base_directory / "build.py"
			build_script.write_text("import time\ntime.sleep(2)\n", encoding="utf-8")
			runner = BuildRunner(build_script)
			runner.start(metadata_path)
			try:
				with self.assertRaises(RuntimeError):
					runner.start(metadata_path)
			finally:
				runner.stop()

	def test_stop_terminates_the_running_process(self):
		with tempfile.TemporaryDirectory() as temporary_directory:
			base_directory = Path(temporary_directory)
			metadata_path = base_directory / "metadata.json"
			metadata_path.write_text("{}", encoding="utf-8")
			build_script = base_directory / "build.py"
			build_script.write_text("import time\ntime.sleep(30)\n", encoding="utf-8")
			runner = BuildRunner(build_script)
			runner.start(metadata_path)
			self.assertTrue(runner.stop())
			if runner.thread is not None:
				runner.thread.join(timeout=3)
			self.assertFalse(runner.running)


class PresentationHelperTests(unittest.TestCase):
	def test_summaries_are_compact_and_human_readable(self):
		self.assertEqual(
			author_summary({"name":"Example Author", "affiliations":["A", "B"], "CA":True}),
			"Example Author · 2 affiliations · corresponding author",
		)
		self.assertEqual(
			source_summary({"type":"file", "path":"sources/main.tex"}),
			"file · sources/main.tex",
		)
		self.assertEqual(
			target_summary({
				"template":{"name":"Elsevier", "category":"Publisher"},
				"output":{"path":"targets/Elsevier/main.tex"},
			}),
			"Elsevier.Publisher → targets/Elsevier/main.tex",
		)

	def test_ui_natural_language_is_english_and_default_font_is_times_new_roman(self):
		self.assertEqual(DEFAULT_FONT_FAMILY, "Times New Roman")
		ui_source = (FLAT_DIRECTORY / "UI.py").read_text(encoding="utf-8")
		self.assertIsNone(re.search(r"[\u3400-\u9fff]", ui_source))

	def test_gui_uses_the_original_classic_tkinter_structure(self):
		ui_source = (FLAT_DIRECTORY / "UI.py").read_text(encoding="utf-8")
		self.assertIn("class GraphicalUserInterface", ui_source)
		self.assertIn('text = "Generator"', ui_source)
		self.assertIn('relief = "raised"', ui_source)
		self.assertIn("__DefaultPaddingValue = 5", ui_source)
		self.assertNotIn("NAVIGATION =", ui_source)
		self.assertRegex(
			ui_source,
			r"\n\t\t\t\tself\.build_runner\.stop\(\)\n\t\t\tself\.root\.destroy\(\)",
		)

	def test_unknown_field_count_includes_nested_object_extensions(self):
		data = {
			"title":"Title",
			"customTop":1,
			"authors":[{
				"name":"Author",
				"affiliations":[],
				"FA":False,
				"CA":False,
				"email":"",
				"ORCID":"",
				"customAuthor":2,
			}],
			"targets":[{
				"template":{"name":"Elsevier", "category":"Publisher", "customTemplate":3},
				"output":{"path":"main.tex", "type":"file"},
			}],
		}
		self.assertEqual(unknown_field_count(data), 3)

	def test_unknown_field_count_tolerates_invalid_known_list_types(self):
		self.assertEqual(
			unknown_field_count({"title":"Title", "authors":7, "tex":None, "customTop":True}),
			1,
		)


if __name__ == "__main__":
	unittest.main()
