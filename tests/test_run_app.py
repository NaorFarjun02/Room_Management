"""
Tests for the launcher: run_app.py and the run.sh / run.cmd wrappers.

Run from the project folder:   python -m unittest discover -s tests -v
Only the standard library is needed. The run.sh tests run on Linux / macOS, the run.cmd tests run on Windows.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import run_app  # noqa: E402

APP_SUBDIR = os.path.join("src", "1.1 - sql-UI")


def traceback_for(module):
    return ("Traceback (most recent call last):\n"
            '  File "main.py", line 2, in <module>\n'
            f"ModuleNotFoundError: No module named '{module}'\n")


# ------------------------------------------------------------------------------------------------------------
class TestMissingLibrary(unittest.TestCase):

    def setUp(self):
        self.app_dir = tempfile.mkdtemp()
        os.mkdir(os.path.join(self.app_dir, "models"))  # a package of the project
        open(os.path.join(self.app_dir, "helpers.py"), "w").close()  # a module of the project

    def tearDown(self):
        shutil.rmtree(self.app_dir)

    def test_library_name(self):
        self.assertEqual(run_app.missing_library(traceback_for("PyQt5"), self.app_dir), "PyQt5")

    def test_dotted_name_gives_top_package(self):
        self.assertEqual(run_app.missing_library(traceback_for("PyQt5.QtSvg"), self.app_dir), "PyQt5")

    def test_last_missing_module_wins(self):
        text = "Error, models.__init__ ->No module named 'first'\n" + traceback_for("psycopg2")
        self.assertEqual(run_app.missing_library(text, self.app_dir), "psycopg2")

    def test_other_error(self):
        text = "Traceback (most recent call last):\npsycopg2.OperationalError: connection refused\n"
        self.assertIsNone(run_app.missing_library(text, self.app_dir))

    def test_empty_output(self):
        self.assertIsNone(run_app.missing_library("", self.app_dir))

    def test_project_package_is_not_a_library(self):
        self.assertIsNone(run_app.missing_library(traceback_for("models"), self.app_dir))
        self.assertIsNone(run_app.missing_library(traceback_for("models.app_function"), self.app_dir))

    def test_project_module_is_not_a_library(self):
        self.assertIsNone(run_app.missing_library(traceback_for("helpers"), self.app_dir))


class TestPipPackage(unittest.TestCase):

    def test_psycopg2_uses_binary_package(self):
        self.assertEqual(run_app.pip_package("psycopg2"), "psycopg2-binary")

    def test_same_name(self):
        self.assertEqual(run_app.pip_package("PyQt5"), "PyQt5")


class TestAskYesNo(unittest.TestCase):

    def ask(self, answer):
        return run_app.ask_yes_no("? ", input_func=lambda question: answer)

    def test_yes_answers(self):
        for answer in ["y", "Y", "yes", "YES", " y ", "y\r"]:
            self.assertTrue(self.ask(answer), answer)

    def test_no_answers(self):
        for answer in ["", "n", "N", "no", "maybe", "yy"]:
            self.assertFalse(self.ask(answer), answer)

    def test_no_input_at_all_is_no(self):
        def eof(question):
            raise EOFError
        self.assertFalse(run_app.ask_yes_no("? ", input_func=eof))


# ------------------------------------------------------------------------------------------------------------
class FakeApp:
    """Acts like the real app: fails while PyQt5 / psycopg2 are missing, then runs"""

    def __init__(self, other_error=None, always_missing=None, pip_works=True):
        self.installed, self.runs = [], 0
        self.other_error, self.always_missing, self.pip_works = other_error, always_missing, pip_works

    def run(self):
        self.runs += 1
        if self.always_missing:
            return 1, traceback_for(self.always_missing)
        if "PyQt5" not in self.installed:
            return 1, traceback_for("PyQt5")
        if "psycopg2-binary" not in self.installed:
            return 1, traceback_for("psycopg2")
        if self.other_error:
            return 1, self.other_error
        return 0, ""

    def pip(self, package):
        if self.pip_works:
            self.installed.append(package)
        return self.pip_works


class TestLauncherLoop(unittest.TestCase):

    def setUp(self):
        self.app_dir = tempfile.mkdtemp()
        open(os.path.join(self.app_dir, "main.py"), "w").close()
        self.out, self.err, self.questions = io.StringIO(), io.StringIO(), []

    def tearDown(self):
        shutil.rmtree(self.app_dir)

    def launch(self, app, answers):
        answers = list(answers)

        def ask(question):
            self.questions.append(question)
            return answers.pop(0) if answers else False
        return run_app.main(runner=app.run, installer=app.pip, ask=ask, app_dir=self.app_dir,
                            out=self.out, err=self.err)

    def test_installs_every_missing_library_until_the_app_starts(self):
        app = FakeApp()
        self.assertEqual(self.launch(app, [True, True]), 0)
        self.assertEqual(app.installed, ["PyQt5", "psycopg2-binary"])
        self.assertEqual(app.runs, 3)
        self.assertEqual(len(self.questions), 2)
        self.assertIn("pip install psycopg2-binary", self.questions[1])

    def test_declined_install_stops(self):
        app = FakeApp()
        self.assertEqual(self.launch(app, [False]), 1)
        self.assertEqual(app.installed, [])
        self.assertIn("can't start without 'PyQt5'", self.out.getvalue())

    def test_other_error_is_shown_and_stops_without_asking(self):
        app = FakeApp(other_error="psycopg2.OperationalError: connection refused\n")
        app.installed = ["PyQt5", "psycopg2-binary"]
        self.assertEqual(self.launch(app, []), 1)
        self.assertEqual(self.questions, [])
        self.assertIn("psycopg2.OperationalError: connection refused", self.err.getvalue())

    def test_still_missing_after_install_stops_instead_of_looping(self):
        app = FakeApp(always_missing="foo.bar")
        self.assertEqual(self.launch(app, [True, True, True]), 1)
        self.assertEqual(app.installed, ["foo"])
        self.assertEqual(app.runs, 2)
        self.assertIn("'foo' was installed but Python still can't find", self.err.getvalue())

    def test_pip_failure_stops(self):
        app = FakeApp(pip_works=False)
        self.assertEqual(self.launch(app, [True]), 1)
        self.assertIn("installing 'PyQt5' failed", self.err.getvalue())
        self.assertEqual(app.runs, 1)

    def test_missing_project_module_is_an_error_not_a_question(self):
        os.mkdir(os.path.join(self.app_dir, "models"))
        app = FakeApp(always_missing="models")
        self.assertEqual(self.launch(app, [True]), 1)
        self.assertEqual(self.questions, [])

    def test_crash_exit_code_becomes_1(self):
        # e.g. a crash on Windows returns 3221225477, which is not a valid script exit code
        self.assertEqual(run_app.main(runner=lambda: (3221225477, "crash"), app_dir=self.app_dir,
                                      out=self.out, err=self.err), 1)

    def test_app_not_found(self):
        os.remove(os.path.join(self.app_dir, "main.py"))
        self.assertEqual(run_app.main(runner=FakeApp().run, app_dir=self.app_dir, out=self.out, err=self.err), 1)
        self.assertIn("can't find the app", self.err.getvalue())


# ------------------------------------------------------------------------------------------------------------
class TestWithRealPython(unittest.TestCase):
    """The loop with a real app process: real ModuleNotFoundError tracebacks and exit codes"""

    def setUp(self):
        self.app_dir = tempfile.mkdtemp()
        self.site_dir = tempfile.mkdtemp()  # "installing" = writing a module here
        with open(os.path.join(self.app_dir, "main.py"), "w") as f:
            f.write(textwrap.dedent(f"""
                import sys
                sys.path.insert(0, {self.site_dir!r})
                import fake_lib_one
                import fake_lib_two.sub
                print("APP RUNNING")
            """))
        self.out, self.err = io.StringIO(), io.StringIO()

    def tearDown(self):
        shutil.rmtree(self.app_dir)
        shutil.rmtree(self.site_dir)

    def install(self, package):
        os.makedirs(os.path.join(self.site_dir, package), exist_ok=True)
        open(os.path.join(self.site_dir, package, "__init__.py"), "w").close()
        open(os.path.join(self.site_dir, package, "sub.py"), "w").close()
        return True

    def test_real_process(self):
        asked = []
        code = run_app.main(runner=lambda: run_app.run_app(sys.executable, self.app_dir), installer=self.install,
                            ask=lambda question: asked.append(question) or True,
                            app_dir=self.app_dir, out=self.out, err=self.err)
        self.assertEqual(code, 0)
        self.assertEqual(len(asked), 2)
        self.assertIn("fake_lib_one", asked[0])
        self.assertIn("fake_lib_two", asked[1])  # "fake_lib_two.sub" -> fake_lib_two

    def test_real_process_other_error(self):
        with open(os.path.join(self.app_dir, "main.py"), "w") as f:
            f.write("raise RuntimeError('database is down')\n")
        code = run_app.main(runner=lambda: run_app.run_app(sys.executable, self.app_dir),
                            app_dir=self.app_dir, out=self.out, err=self.err)
        self.assertEqual(code, 1)
        self.assertIn("RuntimeError: database is down", self.err.getvalue())


# ------------------------------------------------------------------------------------------------------------
class ScriptTestBase(unittest.TestCase):
    """A copy of the launcher files in a temp folder, with a small fake app in src/1.1 - sql-UI"""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        for name in ["run_app.py", "run.sh", "run.cmd"]:
            shutil.copy(os.path.join(ROOT, name), self.root)
        self.app_dir = os.path.join(self.root, APP_SUBDIR)
        os.makedirs(self.app_dir)

    def tearDown(self):
        shutil.rmtree(self.root)

    def write_app(self, code):
        with open(os.path.join(self.app_dir, "main.py"), "w") as f:
            f.write(textwrap.dedent(code))

    def run_script(self, command, answers=""):
        result = subprocess.run(command, cwd=self.root, input=answers, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, universal_newlines=True, timeout=120)
        return result.returncode, result.stdout


@unittest.skipIf(os.name == "nt" or not shutil.which("bash"), "run.sh is tested on Linux / macOS")
class TestRunSh(ScriptTestBase):

    def run_sh(self, answers=""):
        return self.run_script(["bash", os.path.join(self.root, "run.sh")], answers)

    def test_app_starts(self):
        self.write_app('import os; print("APP RUNNING in", os.path.basename(os.getcwd()))')
        code, output = self.run_sh()
        self.assertEqual(code, 0, output)
        self.assertIn("APP RUNNING in 1.1 - sql-UI", output)  # started from the app folder

    def test_missing_library_declined(self):
        self.write_app("import some_library_that_does_not_exist_xyz")
        code, output = self.run_sh("n\n")
        self.assertEqual(code, 1, output)
        self.assertIn("The library 'some_library_that_does_not_exist_xyz' is missing.", output)
        self.assertIn("can't start without", output)

    def test_other_error(self):
        self.write_app("raise RuntimeError('database is down')")
        code, output = self.run_sh()
        self.assertEqual(code, 1, output)
        self.assertIn("RuntimeError: database is down", output)

    def test_uses_project_venv_first(self):
        venv_python = os.path.join(self.root, ".venv", "bin", "python")
        os.makedirs(os.path.dirname(venv_python))
        with open(venv_python, "w") as f:
            f.write(f'#!/bin/sh\nexport LAUNCHED_BY_VENV=yes\nexec "{sys.executable}" "$@"\n')
        os.chmod(venv_python, 0o755)
        self.write_app('import os; print("venv:", os.environ.get("LAUNCHED_BY_VENV"))')
        code, output = self.run_sh()
        self.assertEqual(code, 0, output)
        self.assertIn("venv: yes", output)


@unittest.skipUnless(os.name == "nt", "run.cmd is tested on Windows")
class TestRunCmd(ScriptTestBase):

    def run_cmd(self, answers=""):
        # the extra line answers the "pause" that keeps the window open after an error
        return self.run_script(["cmd", "/c", os.path.join(self.root, "run.cmd")], answers + "\r\n")

    def test_app_starts(self):
        self.write_app('import os; print("APP RUNNING in", os.path.basename(os.getcwd()))')
        code, output = self.run_cmd()
        self.assertEqual(code, 0, output)
        self.assertIn("APP RUNNING in 1.1 - sql-UI", output)

    def test_missing_library_declined(self):
        self.write_app("import some_library_that_does_not_exist_xyz")
        code, output = self.run_cmd("n\r\n")
        self.assertEqual(code, 1, output)
        self.assertIn("The library 'some_library_that_does_not_exist_xyz' is missing.", output)

    def test_other_error(self):
        self.write_app("raise RuntimeError('database is down')")
        code, output = self.run_cmd()
        self.assertEqual(code, 1, output)
        self.assertIn("RuntimeError: database is down", output)


if __name__ == "__main__":
    unittest.main()
