import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import unittest
import itertools
import json
from pathlib import Path
from moteur_fusion.controleur import ControleurDialogue
from moteur_fusion.etats import EtatDialogue
from moteur_fusion.scene import Scene
from moteur_fusion.communication_ivy import dispatch
from reconnaissance_gestuelle.reconnaisseur import Recognizer


class Clock:
    def __init__(self):
        self.now = 0

    def __call__(self):
        return self.now

    def advance(self, n):
        self.now += n


class FusionTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.e = ControleurDialogue(clock=self.clock)

    def test_all_orders_create(self):
        # 24 permutations : action, geste, couleur, position (voix puis clic).
        for order in itertools.permutations("agcp"):
            e = ControleurDialogue(clock=self.clock)
            for event in order:
                if event == "a":
                    e.speech("créer")
                if event == "g":
                    e.gesture("rectangle")
                if event == "c":
                    e.speech("rouge")
                if event == "p":
                    e.speech("ici")
                    e.point(120, 140)
            o = e.validate()
            self.assertIsNotNone(o, order)
            self.assertEqual(
                (o.shape, o.color, o.x, o.y), ("rectangle", "rouge", 120, 140)
            )

    def test_spoken_shape_point(self):
        self.e.speech("créer un cercle vert ici")
        self.e.point(100, 150)
        self.assertEqual(self.e.validate().color, "vert")

    def test_optional_defaults(self):
        self.e.gesture("triangle")
        self.e.speech("créer")
        o = self.e.validate()
        self.assertEqual((o.color, o.x, o.y), ("bleu", 400, 250))

    def test_monomodal_rejected(self):
        self.e.speech("créer un rectangle rouge")
        self.assertIsNone(self.e.validate())
        self.assertEqual(len(self.e.scene.objects), 0)

    def test_redundant_gesture_not_complementary(self):
        self.e.speech("créer un rectangle rouge")
        self.e.gesture("rectangle")
        self.assertIsNone(self.e.validate())

    def test_full_speech_after_redundant_gesture(self):
        self.e.gesture("rectangle")
        self.e.speech("créer un rectangle rouge")
        self.assertIsNone(self.e.validate())

    def test_point_before_reference(self):
        self.e.point(100, 150)
        self.clock.advance(2)
        self.e.speech("créer un cercle ici")
        self.assertIsNotNone(self.e.validate())

    def test_old_point_not_bound(self):
        self.e.point(100, 150)
        self.clock.advance(4)
        self.e.speech("créer un cercle ici")
        self.assertIsNone(self.e.validate())

    def test_reference_before_point(self):
        self.e.speech("créer un cercle ici")
        self.clock.advance(2)
        self.e.point(100, 150)
        self.assertIsNotNone(self.e.validate())

    def test_late_point_not_bound(self):
        self.e.speech("créer un cercle ici")
        self.clock.advance(4)
        self.e.point(100, 150)
        self.assertIsNone(self.e.validate())

    def test_two_references_consume_two_points(self):
        self.e.scene.create("cercle", "rouge", (80, 80))
        self.e.speech("créer un rectangle de cette couleur ici")
        self.e.point(80, 80)
        self.assertIsNone(self.e.validate())
        self.e.point(200, 200)
        o = self.e.validate()
        self.assertEqual((o.color, o.x, o.y), ("rouge", 200, 200))

    def test_reverse_reference_order(self):
        self.e.scene.create("cercle", "vert", (80, 80))
        self.e.speech("créer un losange ici de cette couleur")
        self.e.point(200, 200)
        self.e.point(80, 80)
        o = self.e.validate()
        self.assertEqual((o.color, o.x, o.y), ("vert", 200, 200))

    def test_move_speech(self):
        o = self.e.scene.create("cercle", "rouge", (80, 80))
        self.e.speech("déplacer cet objet")
        self.e.point(80, 80)
        self.e.speech("ici")
        self.e.point(300, 200)
        self.assertEqual(self.e.validate().id, o.id)
        self.assertEqual((o.x, o.y), (300, 200))

    def test_move_gesture(self):
        self.e.scene.create("rectangle", "bleu", (80, 80))
        self.e.gesture("deplacer")
        self.e.speech("cet objet")
        self.e.point(80, 80)
        self.e.speech("ici")
        self.e.point(350, 200)
        self.assertIsNotNone(self.e.validate())

    def test_overlap_disambiguation(self):
        a = self.e.scene.create("rectangle", "rouge", (80, 80))
        b = self.e.scene.create("rectangle", "bleu", (80, 80))
        self.e.speech("déplacer ce rectangle")
        self.e.point(80, 80)
        self.e.speech("ici")
        self.e.point(300, 200)
        self.assertIsNone(self.e.validate())
        self.assertEqual(self.e.state, EtatDialogue.AMBIGUOUS)
        self.e.speech("rouge")
        self.assertEqual(self.e.validate().id, a.id)
        self.assertEqual((b.x, b.y), (80, 80))

    def test_same_color_overlap_not_arbitrary(self):
        for _ in range(2):
            self.e.scene.create("rectangle", "rouge", (80, 80))
        self.e.speech("déplacer ce rectangle rouge ici")
        self.e.point(80, 80)
        self.e.point(300, 200)
        self.assertIsNone(self.e.validate())

    def test_sample_color_overlap(self):
        self.e.scene.create("rectangle", "rouge", (80, 80))
        self.e.scene.create("cercle", "bleu", (80, 80))
        self.e.speech("créer un triangle de cette couleur")
        self.e.point(80, 80)
        self.assertIsNone(self.e.validate())
        self.e.speech("bleu")
        self.assertIsNotNone(self.e.validate())

    def test_sample_empty_is_error(self):
        self.e.speech("créer un triangle de cette couleur")
        self.e.point(80, 80)
        self.assertEqual(self.e.state, EtatDialogue.ERROR)
        self.assertIsNone(self.e.validate())

    def test_low_confidence(self):
        self.e.speech("créer", 0.2)
        self.e.gesture("rectangle", 0.2)
        self.assertIsNone(self.e.data.action)
        self.assertIsNone(self.e.data.shape)

    def test_conflict_latched(self):
        self.e.speech("créer")
        self.e.gesture("rectangle")
        self.e.gesture("triangle")
        self.e.point(80, 80)
        self.e.speech("rouge")
        self.assertEqual(self.e.state, EtatDialogue.ERROR)
        self.assertIsNone(self.e.validate())
        self.e.speech("annuler")
        self.assertEqual(self.e.state, EtatDialogue.IDLE)

    def test_cancel_clears_everything(self):
        self.e.speech("créer ici")
        self.e.point(80, 80)
        self.e.speech("annuler")
        self.assertIsNone(self.e.data.target)
        self.assertFalse(self.e.data.origins)

    def test_timeout(self):
        self.e.speech("créer ici")
        self.clock.advance(13)
        self.e.tick()
        self.assertEqual(self.e.state, EtatDialogue.IDLE)
        self.assertFalse(self.e.data.references)

    def test_no_stale_after_execution(self):
        self.e.speech("créer")
        self.e.gesture("rectangle")
        self.e.validate()
        self.e.speech("créer")
        self.assertIsNone(self.e.validate())
        self.assertEqual(len(self.e.scene.objects), 1)

    def test_no_double_validation(self):
        self.e.speech("créer")
        self.e.gesture("rectangle")
        self.e.validate()
        self.e.validate()
        self.assertEqual(len(self.e.scene.objects), 1)

    def test_parsers(self):
        self.assertTrue(
            dispatch(self.e, "sra5 Parsed='créer' Confidence='0,8' NP='1' Num_A='0'")
        )
        self.assertTrue(
            dispatch(self.e, "OneDollarIvy Template=triangle Confidence=0,9")
        )
        self.assertIsNotNone(self.e.validate())
        self.assertFalse(dispatch(self.e, "not a message"))

    def test_text_sra(self):
        self.assertTrue(
            dispatch(self.e, "sra5 Text=créer un cercle ici Confidence=0.9")
        )
        self.assertTrue(dispatch(self.e, "Palette Point x=100 y=120"))
        self.assertIsNotNone(self.e.validate())

    def test_bad_text_and_bounds(self):
        self.e.speech("créer un hippopotame")
        self.e.point(-1, 30)
        self.assertIsNone(self.e.data.action)
        self.assertFalse(self.e.data.points)

    def test_shape_hit_testing(self):
        s = Scene()
        for name in ["rectangle", "cercle", "triangle", "losange"]:
            o = s.create(name, position=(100, 100))
            self.assertTrue(o.contains(100, 100))
            self.assertFalse(o.contains(200, 200))
        self.assertFalse(s.objects[-1].contains(135, 135))

    def test_initial_gesture_templates(self):
        r = Recognizer(
            Path(__file__).resolve().parents[1]
            / "src"
            / "reconnaissance_gestuelle"
            / "templates"
            / "gestures.json"
        )
        for name, traces in r.templates.items():
            score, result = r.recognize(traces[0])
            self.assertEqual(result, name)
            self.assertGreater(score, 0.9)


if __name__ == "__main__":
    unittest.main()
