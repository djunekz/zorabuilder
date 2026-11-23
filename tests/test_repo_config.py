import re
import unittest

from tests.helpers import ROOT

LABELS = ROOT / ".github" / "labels.yml"
WORKFLOWS = ROOT / ".github" / "workflows"


class LabelConfigTests(unittest.TestCase):
    def test_every_color_is_a_quoted_hex_string(self):
        lines = [line for line in LABELS.read_text().splitlines() if line.strip().startswith("color:")]
        self.assertGreater(len(lines), 0)
        for line in lines:
            self.assertRegex(line.strip(), r'^color: "[0-9a-fA-F]{6}"$', line)

    def test_label_names_are_unique(self):
        names = re.findall(r"^- name: (.+)$", LABELS.read_text(), flags=re.M)
        self.assertEqual(len(names), len(set(names)))

    def test_descriptions_fit_github_limit(self):
        for description in re.findall(r"^\s+description: (.+)$", LABELS.read_text(), flags=re.M):
            self.assertLessEqual(len(description), 100, description)


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = (WORKFLOWS / "release.yml").read_text()

    def test_release_attaches_only_the_archive_and_its_checksum(self):
        self.assertIn("dist/zorabuilder-${{ env.TAG }}.tar.gz\n", self.text)
        self.assertIn("dist/zorabuilder-${{ env.TAG }}.tar.gz.sha256sum", self.text)
        self.assertNotIn("dist/*", self.text)
        self.assertNotIn("SHA256SUMS", self.text)
        self.assertNotIn("python -m build", self.text)

    def test_release_title_is_zorabuilder_followed_by_the_tag(self):
        self.assertIn("name: ZoraBuilder ${{ env.TAG }}", self.text)

    def test_release_fails_when_an_asset_is_missing(self):
        self.assertIn("fail_on_unmatched_files: true", self.text)

    def test_checksum_is_verified_before_publishing(self):
        self.assertIn('sha256sum --check "zorabuilder-${TAG}.tar.gz.sha256sum"', self.text)


class WorkflowConfigTests(unittest.TestCase):
    def test_dependency_review_runs_only_after_a_successful_probe(self):
        text = (WORKFLOWS / "dependency-review.yml").read_text()
        self.assertIn("id: probe", text)
        self.assertRegex(text, r"dependency-review-action@v\d+\n\s+if: steps\.probe\.outputs\.status == '200'")
        self.assertIn("steps.probe.outputs.status != '200'", text)

    def test_dependabot_updates_are_grouped(self):
        text = (ROOT / ".github" / "dependabot.yml").read_text()
        self.assertEqual(text.count("package-ecosystem:"), text.count("groups:"))

    def test_python_versions_are_quoted(self):
        text = (WORKFLOWS / "ci.yml").read_text()
        match = re.search(r"python-version: \[(.+)\]", text)
        self.assertIsNotNone(match)
        for item in match.group(1).split(","):
            self.assertRegex(item.strip(), r'^"3\.\d+"$')

    def test_every_workflow_declares_permissions(self):
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            self.assertRegex(workflow.read_text(), r"(?m)^permissions:", workflow.name)

    def test_every_workflow_job_has_a_timeout(self):
        for workflow in sorted(WORKFLOWS.glob("*.yml")):
            text = workflow.read_text()
            self.assertEqual(text.count("runs-on:"), text.count("timeout-minutes:"), workflow.name)


if __name__ == "__main__":
    unittest.main()
