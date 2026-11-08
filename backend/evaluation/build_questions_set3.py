"""Génère evaluation/questions_set3.csv : un troisième jeu de 36 questions, réservé au TEST FINAL des corrections.

    python -m evaluation.build_questions_set3

Contexte : le jeu de réglage a montré des faiblesses (refus à tort, textes arabes interrogés en français). Pour les
corriger sans tricher, on ne peut plus se servir du jeu de réglage comme test : il devient, avec le jeu de départ, un jeu de
RÉGLAGE. Ce jeu de test final est écrit AVANT toute correction et mesuré UNE seule fois à la fin, avec le système corrigé ;
on le mesure aussi avec l'ancien système pour comparer « avant » et « après » sur les mêmes questions.

Composition (l'ancien jeu de réglage était dominé par les questions en français sur des textes en français ; ici
la moitié des questions croisent volontairement les langues, pour mesurer les corrections là où elles servent) :
  9 français sur texte arabe, 6 arabe sur texte français, 7 français sur texte français, 4 arabe sur texte arabe,
  2 questions combinées, 8 questions hors corpus.

Comme pour les autres jeux, le script RETROUVE chaque passage dans les chunks et recopie page et extrait.
"""

import csv
import sys

from evaluation.build_questions_set2 import (
    C_AR, C_FR, DECRET, GUIDE, L14, L26, L31, L46, L64, L65, L66, L76, L79, L85, L88, L89, L97, L113, L128, L130, L28,
    L59, A503, RI, locate,
)
from src import config

sys.stdout.reconfigure(encoding="utf-8")

# Motifs de recherche (un espace accepte n'importe quelle suite d'espaces ou de retours à la ligne)
P_64_SIGN = "يجب أن تكون لائحة دعم الملتمس موقعة على الأقل"
P_28_DELAI = "يجرى انتخاب أعضاء مجلس المستشارين خلال الستين يوما"
P_28_MODE = "تجرى انتخابات أعضاء مجلس المستشارين عن طريق"
P_59_PARTIELLE = "تنتهي مدة عضوية المنتخبين في انتخابات جزئية"
P_97_PREAVIS = "أيام على الأقل قبل التاريخ المقرر لتنفيذ الإضراب"
P_97_DANGER = "بخصوص وجود خطر حال يهدد صحة وسلامة الأجراء"
P_97_45 = "بعد انصرام أجل خمسة وأربعين"
P_26_ENSEIGNEMENT = "يعد تعليم اللغة الأمازيغية حقا لجميع المغاربة بدون استثناء"
P_DECRET_ADD = "يصرف الدعم السنوي الإضافي"
P_503_DONNEES = "كما يتيح لفائدة الناخبات والناخبين المقيدين"
P_113_PRESIDENT = "ينتخب رئيس المجلس في الدور الأول"
P_31_PLAINTE = r"dans un délai de vingt \(20\) jours ouvrables suivant l.expiration"
P_85_PEINE = r"est punie d.une amende de cinq mille"
P_14_INCOMPAT = "La fonction du Médiateur est incompatible avec le mandat de membre du gouvernement"
P_130_RECT = r"Le projet de loi de finances rectificative est voté par le Parlement dans un délai n.excédant pas quinze"
P_128_EXPERTS = r"ces membres, qui sont au nombre de 24, sont nommés par Sa Majesté le Roi"
P_128_MANDAT = r"le mandat de membre du Conseil est de cinq ans, renouvelable une seule fois"
P_88_DIRECTEUR = "doit avoir un directeur de publication"
P_GUIDE_AUTEURS = "Lotte Geunis"
P_RI_30 = r"Les réponses du Chef du Gouvernement à ces questions sont présentées dans les trente jours"
P_65_SGG = r"Le secrétaire général du gouvernement procède, avant la tenue du Conseil du gouvernement, à la diffusion"
P_46_CORRUPTION = r"on entend par corruption toute infraction"
P_79_ANTENNES = r"Des antennes régionales de l.Autorité sont créées"
P_89_FINANCE = r"jouit, en tant que personne morale de droit public, de l.autonomie financière"
P_66_15ANS = r"ayant exercé leur profession depuis plus de quinze"
P_66_MANDAT = r"est composée de douze \(12\) membres, nommés pour une durée de 9 ans non renouvelable"
P_14_NOMME = r"Le Médiateur est nommé par dahir pour une période de cinq \(5\) ans"

# La Constitution contient les mêmes règles que la loi organique sur la Cour constitutionnelle
EQUIVALENTS = {C_FR: [C_AR], C_AR: [C_FR], L66: [C_FR, C_AR]}

# (type, langue, question, réponse attendue, [(fichier, motif), ...])
Q = [
 # --- 9 questions en français sur des textes uniquement en arabe
 ("simple", "fr", "Combien de signatures faut-il au minimum pour soutenir une motion législative ?",
  "Au moins 20 000 signatures de soutien, de citoyennes et citoyens remplissant les conditions requises (droits civils et politiques, inscription sur les listes électorales) (loi organique 64-14).", [(L64, P_64_SIGN)]),
 ("simple", "fr", "Quand a lieu l'élection des membres de la Chambre des conseillers par rapport au début de leur mandat ?",
  "Au plus tard dans les soixante jours qui précèdent la date de début de leur mandat (loi organique 28-11).", [(L28, P_28_DELAI)]),
 ("simple", "fr", "Jusqu'à quand dure le mandat d'un élu local issu d'une élection partielle ?",
  "Jusqu'à la fin du mandat des élus de l'élection générale : il prend fin en même temps que le leur (loi organique 59-11, art. 2).", [(L59, P_59_PARTIELLE)]),
 ("simple", "fr", "Combien de jours à l'avance faut-il annoncer une grève au niveau national ?",
  "Au moins sept jours avant la date prévue, par notification au Chef du gouvernement et aux autorités gouvernementales chargées de l'Intérieur, de l'Emploi et du secteur concerné (loi organique 97-15).", [(L97, P_97_PREAVIS)]),
 ("simple", "fr", "Peut-on appeler à la grève sans attendre en cas de danger imminent pour la santé des salariés ?",
  "Oui, dans le secteur privé : on peut appeler à la grève dès que le danger imminent est établi et que l'employeur n'a pas pris les mesures nécessaires pour l'écarter ou l'arrêter (loi organique 97-15).", [(L97, P_97_DANGER)]),
 ("simple", "fr", "Qui a droit à l'enseignement de la langue amazighe ?",
  "Tous les Marocains, sans exception : l'enseignement de l'amazighe est un droit pour tous (loi organique 26-16, art. 3).", [(L26, P_26_ENSEIGNEMENT)]),
 ("simple", "fr", "Le soutien annuel supplémentaire aux partis politiques est-il versé automatiquement ?",
  "Non : il est versé à la demande du parti concerné et réservé aux missions, études et recherches ; chaque parti remet en fin d'exercice un dossier à la Cour des comptes (décret 2.12.293 modifié, art. 2 bis).", [(DECRET, P_DECRET_ADD)]),
 ("simple", "fr", "Peut-on consulter ses données personnelles sur les listes électorales en ligne ?",
  "Oui : les électeurs inscrits peuvent consulter personnellement leurs données sur le site du ministère de l'Intérieur et y ajouter une adresse électronique ou un numéro de mobile (arrêté 503-26).", [(A503, P_503_DONNEES)]),
 ("simple", "fr", "Comment est élu le président du conseil communal ?",
  "Au premier tour à la majorité absolue des membres en exercice ; à défaut, un second tour a lieu lors de la même séance entre les deux candidats arrivés en tête (loi organique 113-14, art. 13).", [(L113, P_113_PRESIDENT)]),
 # --- 6 questions en arabe sur des textes en français
 ("arabe", "ar", "ماذا يجب فعله إذا لم تجب الإدارة عن طلب الحصول على المعلومات؟",
  "يمكن تقديم شكاية إلى رئيس المؤسسة داخل أجل عشرين يوم عمل بعد انتهاء الأجل المحدد للجواب، ثم إلى اللجنة المختصة داخل ثلاثين يوما (القانون 31.13).", [(L31, P_31_PLAINTE)]),
 ("arabe", "ar", "ما هي عقوبة الامتناع عن المثول أمام لجنة تقصي الحقائق؟",
  "غرامة من 5000 إلى 20000 درهم وحبس من ستة أشهر إلى سنتين، أو إحدى هاتين العقوبتين فقط (القانون التنظيمي 085.13).", [(L85, P_85_PEINE)]),
 ("arabe", "ar", "ما هي حالات التنافي مع مهمة الوسيط؟",
  "لا يجوز الجمع بين مهمة الوسيط وعضوية الحكومة أو مجلس النواب أو مجلس المستشارين أو المحكمة الدستورية، ولا مع أي وظيفة عمومية أو مهمة انتخابية أو مسؤولية داخل حزب سياسي أو نقابة (القانون 14.16، المادة 6).", [(L14, P_14_INCOMPAT)]),
 ("arabe", "ar", "في أي مدة يصوت البرلمان على مشروع قانون المالية المعدل؟",
  "خمسة عشر يوما بعد إيداعه بمكتب مجلس النواب، ويبت مجلس النواب فيه داخل ثمانية أيام (القانون التنظيمي 130.13، المادة 51).", [(L130, P_130_RECT)]),
 ("arabe", "ar", "كم عدد الخبراء في المجلس الاقتصادي والاجتماعي والبيئي ومن يعينهم؟",
  "24 خبيرا يعينهم الملك (القانون التنظيمي 128.12، المادة 11).", [(L128, P_128_EXPERTS)]),
 ("arabe", "ar", "هل يجب أن يكون للجريدة الإلكترونية مدير للنشر؟",
  "نعم، كل كتابة دورية أو جريدة إلكترونية أو دعامة إلكترونية يجب أن يكون لها مدير للنشر (القانون 88.13، المادة 15).", [(L88, P_88_DIRECTEUR)]),
 # --- 7 questions en français sur des textes en français
 ("simple", "fr", "Qui a rédigé le guide sur le gouvernement ouvert destiné aux parlementaires ?",
  "Lotte Geunis, experte internationale, et Mohamed Doukha, conseiller général chargé des programmes de coopération internationale à la Chambre des représentants, avec le soutien de MEPI et l'assistance technique du NDI (novembre 2022).", [(GUIDE, P_GUIDE_AUTEURS)]),
 ("simple", "fr", "Combien de temps le Chef du gouvernement a-t-il pour répondre aux questions mensuelles de politique générale ?",
  "Dans les trente jours suivant la date de transmission des questions (règlement intérieur de la Chambre des représentants, art. 278).", [(RI, P_RI_30)]),
 ("simple", "fr", "Qui diffuse les projets de textes aux membres du gouvernement avant le Conseil du gouvernement ?",
  "Le secrétaire général du gouvernement (loi organique 065-13, art. 13).", [(L65, P_65_SGG)]),
 ("simple", "fr", "Comment la loi définit-elle la corruption ?",
  "Toute infraction prévue par les sections III et IV du chapitre III du titre premier du livre III du Code pénal, ainsi que toute autre infraction de corruption prévue par une législation particulière (loi 46-19, art. 3).", [(L46, P_46_CORRUPTION)]),
 ("simple", "fr", "L'Autorité pour la parité a-t-elle des antennes régionales ?",
  "Oui, des antennes régionales sont créées en fonction des conditions administratives et financières (loi 79-14, art. 1).", [(L79, P_79_ANTENNES)]),
 ("simple", "fr", "Le Conseil consultatif de la jeunesse dispose-t-il de l'autonomie financière ?",
  "Oui : c'est une personne morale de droit public qui jouit de l'autonomie financière ; son siège est à Rabat (loi 89-15, art. 1).", [(L89, P_89_FINANCE)]),
 ("simple", "fr", "Quelle expérience faut-il avoir pour siéger à la Cour constitutionnelle ?",
  "Une haute formation juridique et une compétence judiciaire, doctrinale ou administrative, et avoir exercé sa profession depuis plus de quinze ans (loi organique 066-13, art. 1 ; Constitution, art. 130).", [(L66, P_66_15ANS)]),
 # --- 4 questions en arabe sur des textes en arabe
 ("arabe", "ar", "بأي نمط اقتراع تنتخب مجلس المستشارين؟",
  "الاقتراع باللائحة وبالتمثيل النسبي على أساس قاعدة أكبر بقية، دون مزج الأصوات ودون التصويت التفاضلي (القانون التنظيمي 28.11، المادة 3).", [(L28, P_28_MODE)]),
 ("arabe", "ar", "بعد كم يوما يجوز الدعوة إلى الإضراب بخصوص الملف المطلبي؟",
  "بعد انصرام أجل 45 يوما، مع إمكانية التمديد مرة واحدة لفترة 15 يوما (القانون التنظيمي 97.15، المادة 13).", [(L97, P_97_45)]),
 ("arabe", "ar", "كيف ينتخب رئيس المجلس الجماعي؟",
  "في الدور الأول للاقتراع بالأغلبية المطلقة للأعضاء المزاولين مهامهم، وإلا أجري دور ثان في نفس الجلسة بين المترشحين الأول والثاني (القانون التنظيمي 113.14، المادة 13).", [(L113, P_113_PRESIDENT)]),
 ("arabe", "ar", "كم توقيعا يلزم لتقديم ملتمس في مجال التشريع؟",
  "20.000 توقيع على الأقل من مدعمي الملتمس (القانون التنظيمي 64.14).", [(L64, P_64_SIGN)]),
 # --- 2 questions qui demandent deux textes
 ("combinee", "fr", "Pendant combien de temps les membres de la Cour constitutionnelle et ceux du Conseil économique, social et environnemental sont-ils nommés ?",
  "Neuf ans non renouvelables pour la Cour constitutionnelle (loi organique 066-13, art. 1) ; cinq ans renouvelables une seule fois pour le CESE (loi organique 128-12, art. 14, hors catégorie des personnalités représentant des institutions et organismes).", [(L66, P_66_MANDAT), (L128, P_128_MANDAT)]),
 ("combinee", "fr", "Par qui sont nommés le Médiateur et les experts du Conseil économique, social et environnemental ?",
  "Le Médiateur est nommé par dahir (loi 14-16, art. 4) ; les 24 experts du CESE sont nommés par le Roi (loi organique 128-12, art. 11).", [(L14, P_14_NOMME), (L128, P_128_EXPERTS)]),
 # --- 8 questions hors corpus (écrites sans regarder les scores de recherche)
 ("hors_corpus", "fr", "À quel âge peut-on partir à la retraite au Maroc ?", "REFUS (législation sociale absente du corpus)", []),
 ("hors_corpus", "fr", "Comment s'inscrire à l'université publique ?", "REFUS (démarche éducative absente du corpus)", []),
 ("hors_corpus", "fr", "Quel est le montant des allocations familiales ?", "REFUS (prestations sociales absentes du corpus)", []),
 ("hors_corpus", "fr", "Quelle est la durée du congé de maternité ?", "REFUS (code du travail absent du corpus)", []),
 ("hors_corpus", "fr", "Qui est actuellement le président de la Chambre des représentants ?", "REFUS (les titulaires actuels des fonctions ne figurent pas dans les textes)", []),
 ("hors_corpus", "fr", "Quel parti politique est le plus honnête ?", "REFUS (question d'opinion : l'assistant doit rester neutre)", []),
 ("hors_corpus", "ar", "كيف أحصل على رخصة السياقة؟", "REFUS (démarche administrative absente du corpus)", []),
 ("hors_corpus", "ar", "كم يبلغ الحد الأدنى للأجور؟", "REFUS (le salaire minimum n'est fixé par aucun texte du corpus)", []),
]


def main() -> None:
    with open(config.EVAL_DIR / "questions_set3.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "question", "langue", "type", "reponse_attendue", "fichier_attendu", "page_attendue", "extrait_source"])
        for i, (typ, lang, q, ans, anchors) in enumerate(Q, start=1):
            files, pages, ex = [], [], []
            for file, pat in anchors:
                p, e = locate(file, pat)
                files.append("|".join([file] + EQUIVALENTS.get(file, [])))
                pages.append(str(p))
                ex.append(e)
            w.writerow([i, q, lang, typ, ans, ";".join(files), ";".join(pages), " || ".join(ex)])
    in_corpus = [q for q in Q if q[0] != "hors_corpus"]
    print(f"{len(Q)} questions écrites : {len(in_corpus)} sur le corpus, {len(Q) - len(in_corpus)} hors corpus")


if __name__ == "__main__":
    main()
