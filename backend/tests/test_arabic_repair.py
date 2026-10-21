"""Tests de la réparation des ligatures arabes inversées (src/cleaning.py).

Les mots arabes sont écrits avec des codes Unicode (\\uXXXX) pour que le test
reste lisible et indépendant de l'éditeur : « المادة » = \\u0627\\u0644\\u0645\\u0627\\u062f\\u0629.
"""

from src import cleaning

ARTICLE = "المادة"        # المادة (correct)
ARTICLE_BROKEN = "املادة"  # املادة (ligature inversée)


def test_rule_a_fixes_article_followed_by_meem():
    assert cleaning.fix_article_ligature(ARTICLE_BROKEN) == ARTICLE


def test_rule_a_fixes_article_followed_by_alef_and_hamza_forms():
    # االنتخابية -> الانتخابية  et  األحزاب -> الأحزاب
    assert cleaning.fix_article_ligature("االنتخابية") == "الانتخابية"
    assert cleaning.fix_article_ligature("األحزاب") == "الأحزاب"


def test_rule_a_keeps_prefix_waw():
    # واملحكمة -> والمحكمة
    assert cleaning.fix_article_ligature("واملحكمة") == "والمحكمة"


def test_rule_a_does_not_touch_correct_words():
    assert cleaning.fix_article_ligature(ARTICLE) == ARTICLE
    kamila = "كاملة"  # كاملة (« complète ») : mot correct, ne doit pas bouger
    assert cleaning.fix_article_ligature(kamila) == kamila


def test_rule_b_repairs_unknown_word_when_fixed_version_is_known():
    vocabulary = {"خلال", "لا", "إلا"}  # خلال، لا، إلا
    assert cleaning.repair_arabic_ligatures("خالل", vocabulary) == "خلال"  # خالل -> خلال
    assert cleaning.repair_arabic_ligatures("ال", vocabulary) == "لا"  # ال -> لا
    assert cleaning.repair_arabic_ligatures("إال", vocabulary) == "إلا"  # إال -> إلا


def test_rule_b_never_changes_a_known_word():
    vocabulary = {"خالل", "خلال"}  # les deux formes sont connues
    assert cleaning.repair_arabic_ligatures("خالل", vocabulary) == "خالل"


def test_rule_b_leaves_unknown_words_without_a_known_fix():
    vocabulary = {"لا"}
    word = "قال"  # قال (« il a dit ») : inconnu, et sa version « inversée » aussi
    assert cleaning.repair_arabic_ligatures(word, vocabulary) == word


def test_rule_b_keeps_spaces_and_punctuation():
    vocabulary = {"لا"}
    assert cleaning.repair_arabic_ligatures("ال ، 12 abc", vocabulary) == "لا ، 12 abc"


def test_stray_question_mark_inside_a_word_is_removed():
    broken = "سيا؟سي"  # سيا؟سي
    assert cleaning.remove_stray_question_marks(broken) == "سياسي"


def test_real_arabic_question_mark_is_kept():
    question = "هل نعم؟ لا"  # « هل نعم؟ لا » : « ؟ » suivi d'un espace
    assert cleaning.remove_stray_question_marks(question) == question


def test_build_vocabulary_extracts_arabic_words_only():
    vocabulary = cleaning.build_arabic_vocabulary(["لا abc 12 إلا."])
    assert vocabulary == {"لا", "إلا"}


def test_clean_document_uses_vocabulary_when_given():
    vocabulary = {"خلال"}
    pages = ["خالل املادة النص."]
    cleaned = cleaning.clean_document(pages, vocabulary)
    assert cleaned == ["خلال المادة النص."]
