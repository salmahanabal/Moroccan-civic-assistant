"""Tests du choix de l'extrait (src/excerpt.py) : la phrase qui répond doit être celle qu'on montre et qu'on surligne."""

from src import excerpt

ARTICLES = (
    "Article 45 Le Roi dispose d'une liste civile. "
    "Article 46 La personne du Roi est inviolable, et respect Lui est dû. "
    "Article 47 Le Roi nomme le Chef du Gouvernement au sein du parti politique arrivé en tête des élections "
    "des membres de la Chambre des Représentants, et au vu de leurs résultats. "
    "Sur proposition du Chef du Gouvernement, Il nomme les membres du gouvernement."
)


def highlighted(result):
    return result["excerpt"][result["highlight_start"] : result["highlight_end"]]


def test_the_sentence_that_answers_is_shown_first_and_highlighted():
    result = excerpt.best_excerpt(
        ARTICLES,
        answer="Le Roi nomme le Chef du Gouvernement au sein du parti arrivé en tête [1].",
        question="Qui choisit le chef du gouvernement ?",
    )
    assert result["excerpt"].startswith("Article 47 Le Roi nomme")
    assert highlighted(result).endswith("de leurs résultats.")
    assert result["highlight_start"] == 0


def test_a_matching_number_is_enough_to_find_the_sentence():
    text = "Le mandat est de cinq ans. La Chambre compte 395 membres élus. Les membres sont rééligibles."
    result = excerpt.best_excerpt(text, answer="395", question="Combien de personnes siègent ?")
    assert highlighted(result) == "La Chambre compte 395 membres élus."


def test_arabic_digits_match_western_digits():
    text = "النص الأول عام. تتألف الغرفة من 395 عضوا منتخبا. النص الأخير."
    result = excerpt.best_excerpt(text, answer="٣٩٥ عضوا", question="")
    assert "395" in highlighted(result)


def test_arabic_words_match_with_or_without_the_article():
    text = "يمارس الملك السلطة. تتكون اللغات الرسمية للمملكة من العربية والأمازيغية. تحدد اللائحة الداخلية الاختصاص."
    result = excerpt.best_excerpt(text, answer="لغات المملكة الرسمية هي العربية والأمازيغية", question="ما هي اللغات الرسمية؟")
    assert highlighted(result).startswith("تتكون اللغات الرسمية")


def test_no_common_word_keeps_the_start_of_the_passage_without_highlight():
    # réponse en français, texte en arabe : on ne devine pas
    arabic = "يمارس الملك السلطة. تتكون اللغات الرسمية للمملكة من العربية والأمازيغية."
    result = excerpt.best_excerpt(arabic, answer="Les langues officielles sont l'arabe et l'amazighe [1].", question="")
    assert result["excerpt"] == arabic
    assert result["highlight_start"] is None and result["highlight_end"] is None


def test_a_single_weak_common_word_is_not_enough():
    text = "Le budget est voté chaque année. Les citoyens peuvent voter à dix-huit ans."
    result = excerpt.best_excerpt(text, answer="Le budget", question="")
    assert result["highlight_start"] is None   # un seul mot commun : trop faible pour surligner


def test_empty_question_and_stopword_answer_fall_back_to_the_start():
    result = excerpt.best_excerpt("Texte du passage.", answer="et le de [1]", question="")
    assert result == {"excerpt": "Texte du passage.", "highlight_start": None, "highlight_end": None}


def test_excerpt_is_never_longer_than_the_limit_and_highlight_stays_inside():
    long_sentence = "Le Chef du Gouvernement nomme les membres " + "du conseil " * 80 + "."
    result = excerpt.best_excerpt(long_sentence, answer="Le Chef du Gouvernement nomme les membres", question="", max_chars=120)
    assert len(result["excerpt"]) <= 120
    assert result["highlight_end"] <= len(result["excerpt"])


def test_a_very_long_sentence_is_cut_at_commas_to_start_near_the_answer():
    filler = "des dispositions générales sans rapport avec la question posée, " * 8
    text = f"Dans le cadre de ce titre, {filler}la grève est un droit garanti par la Constitution aux salariés."
    result = excerpt.best_excerpt(text, answer="La grève est un droit garanti [1].", question="A-t-on le droit de faire grève ?", max_chars=150)
    assert result["excerpt"].startswith("la grève est un droit garanti")


def test_whitespace_and_line_breaks_are_collapsed_and_offsets_stay_consistent():
    text = "Première phrase\nsur deux lignes.\n\nLe   Roi nomme    le Chef du Gouvernement."
    result = excerpt.best_excerpt(text, answer="Le Roi nomme le Chef du Gouvernement", question="")
    assert result["excerpt"] == "Le Roi nomme le Chef du Gouvernement."
    assert highlighted(result) == result["excerpt"]


def test_stem_ignores_accents_plural_and_stopwords():
    assert excerpt.stem("Gouvernements") == excerpt.stem("gouvernement")
    assert excerpt.stem("élections") == excerpt.stem("ELECTION")
    assert excerpt.stem("le") is None and excerpt.stem("de") is None
    assert excerpt.stem("7") is None and excerpt.stem("47") == "47"
