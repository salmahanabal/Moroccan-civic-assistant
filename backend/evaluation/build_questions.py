"""Génère evaluation/questions.csv : 30 questions de référence avec leur réponse attendue.

    python -m evaluation.build_questions

Pour chaque question, le script RETROUVE le passage dans les chunks (par une expression de
recherche) et recopie mot pour mot l'extrait et la page : aucune page ni extrait n'est écrit à la main.
Les réponses attendues sont rédigées à partir de ces passages réels, puis relues par l'utilisatrice.
Si le corpus change, on relance ce script pour remettre pages et extraits à jour.
"""

import csv
import json
import re
import sys

from src import config

sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(line) for line in open(config.CHUNKS_FILE, encoding="utf-8")]
C_FR, C_AR = "constitution_2011_fr.pdf", "constitution_2011_ar.pdf"
# Versions équivalentes dans l'autre langue : pour le hit rate, l'une OU l'autre suffit (séparées par « | »)
L27_FR = "elections_loi_organique_27_11_chambre_representants_fr.pdf"
L57_FR = "elections_loi_57_11_listes_electorales_consolidee_fr.pdf"
L27 = "elections_loi_organique_27_11_chambre_representants_ar.pdf"
L57 = "elections_loi_57_11_listes_electorales_ar.pdf"
L29 = "partis_loi_organique_29_11_ar.pdf"
D376, D377 = "droits_dahir_1_58_376_association_fr.pdf", "droits_dahir_1_58_377_rassemblements_fr.pdf"
L44 = "participation_loi_organique_44_14_petitions_ar.pdf"
L112 = "institutions_loi_organique_112_14_prefectures_provinces_fr.pdf"
# (type, langue, question, réponse attendue, [(fichier, motif de recherche), ...])
Q = [
 ("simple","fr","À quoi ressemble le drapeau marocain ?","Un drapeau rouge avec, en son centre, une étoile verte à cinq branches (Constitution, art. 4).",[(C_FR,"drapeau rouge frappé")]),
 ("simple","fr","Combien de personnes siègent à la Chambre des représentants ?","395 membres : 305 élus dans les circonscriptions locales et 90 dans les circonscriptions régionales (loi organique 27-11).",[(L27,"395")]),
 ("simple","fr","Les députés sont élus pour combien de temps ?","Pour cinq ans, au suffrage universel direct (Constitution, art. 62).",[(C_FR,"élus pour cinq ans")]),
 ("simple","fr","Qui choisit le chef du gouvernement ?","Le Roi le nomme au sein du parti arrivé en tête des élections de la Chambre des représentants (art. 47).",[(C_FR,"Article 47 Le Roi nomme le Chef")]),
 ("simple","fr","Quelles langues sont officielles au Maroc ?","L'arabe et l'amazighe (art. 5).",[(C_FR,"Article 5 L’arabe")]),
 ("simple","fr","A-t-on le droit de faire grève ?","Oui, le droit de grève est garanti ; une loi organique fixe les conditions de son exercice (art. 29).",[(C_FR,"Le droit de grève est garanti")]),
 ("simple","fr","Faut-il demander la permission pour organiser une réunion publique ?","Non, pas d'autorisation préalable, mais une déclaration préalable signée par trois personnes doit être remise à l'autorité locale (dahir 1-58-377, art. 2 et 3).",[(D377,"sans autorisation préalable")]),
 ("simple","fr","C'est quoi une province, d'après la loi ?","Une collectivité territoriale de droit public, dotée de la personnalité morale et de l'autonomie administrative et financière (loi organique 112-14, art. 2).",[(L112,"Article 2 La préfecture ou la province est")]),
 ("simple","fr","À quoi servent les partis politiques ?","Ils encadrent et forment politiquement les citoyens, promeuvent leur participation, concourent à l'expression de la volonté des électeurs et participent à l'exercice du pouvoir (art. 7).",[(C_FR,"Article 7 Les partis politiques œuvrent")]),
 ("simple","fr","Combien de juges siègent à la Cour constitutionnelle et pour combien de temps ?","Douze membres, pour un mandat de neuf ans non renouvelable (art. 130).",[(C_FR,"composée de douze membres")]),
 ("simple","fr","Qui a le droit de proposer une nouvelle loi ?","Le Chef du Gouvernement et les membres du Parlement (art. 78).",[(C_FR,"L’initiative des lois appartient")]),
 ("simple","fr","Un citoyen peut-il écrire aux autorités pour leur demander quelque chose ?","Oui, les citoyens ont le droit de présenter des pétitions aux pouvoirs publics (art. 15) ; une loi organique en fixe les conditions.",[(C_FR,"droit de présenter des pétitions")]),
 ("simple","fr","Le gouvernement peut-il censurer un journal avant sa publication ?","Non, la liberté de la presse est garantie et ne peut être limitée par aucune forme de censure préalable (art. 28).",[(C_FR,"Article 28 La liberté de la presse")]),
 ("simple","fr","Qui a le droit de voter et de se présenter aux élections ?","Les citoyennes et citoyens majeurs jouissant de leurs droits civils et politiques ; le vote est un droit personnel et un devoir national (art. 30).",[(C_FR,"Sont électeurs et éligibles")]),
 ("simple","fr","Combien de temps a l'administration pour décider si une association est reconnue d'utilité publique ?","Un délai maximum de six mois à compter du dépôt de la demande (dahir 1-58-376).",[(D376,"délai maximum de six mois")]),
 ("combinee","fr","Que faut-il pour pouvoir voter et comment demande-t-on à être inscrit ?","Être majeur et jouir de ses droits civils et politiques (Constitution art. 30) ; les demandes d'inscription sont examinées chaque année par la commission administrative (loi 57-11, art. 22).",[(C_FR,"Sont électeurs et éligibles"),(L57,"طلبات القيد وطلبات نقل القيد")]),
 ("combinee","fr","Comment sont choisis les députés, et qui devient ensuite chef du gouvernement ?","395 députés élus au suffrage direct (loi organique 27-11) ; le Roi nomme le Chef du Gouvernement au sein du parti arrivé en tête (Constitution art. 47).",[(L27,"395"),(C_FR,"Article 47 Le Roi nomme le Chef")]),
 ("combinee","fr","Quelles libertés de réunion et d'association sont garanties, et que faut-il faire pour tenir une réunion publique ?","Les libertés de réunion, de rassemblement, de manifestation pacifique et d'association sont garanties (art. 29) ; une réunion publique exige une déclaration préalable à l'autorité locale (dahir 1-58-377).",[(C_FR,"Sont garanties les libertés de réunion"),(D377,"Toute réunion publique sera précédée")]),
 ("combinee","fr","Qui peut présenter une pétition et à qui l'adresse-t-on ?","Les citoyennes et citoyens (art. 15) ; la loi organique 44-14 précise qu'il s'agit d'une demande écrite adressée aux autorités publiques concernées.",[(C_FR,"droit de présenter des pétitions"),(L44,"كل طلب مكتوب على دعامة")]),
 ("combinee","fr","Peut-on fonder un parti sur une base religieuse, et à quoi servent les partis ?","Non : la fondation d'un parti sur une base religieuse, linguistique, ethnique ou régionale est nulle (loi organique 29-11, art. 4) ; les partis encadrent les citoyens et concourent à l'expression de la volonté des électeurs (Constitution art. 7).",[(L29,"كل تأسيس لحزب سياسي يرتكز"),(C_FR,"Article 7 Les partis politiques œuvrent")]),
 ("arabe","ar","كم عضوا يتكون منه مجلس النواب؟","395 عضوا: 305 على صعيد الدوائر الانتخابية المحلية و90 على صعيد الدوائر الجهوية.",[(L27,"395")]),
 ("arabe","ar","ما هي اللغات الرسمية في المملكة المغربية؟","العربية والأمازيغية (الفصل 5 من الدستور).",[(C_AR,"تظل العربية اللغة الرسمية")]),
 ("arabe","ar","كم سنة يُنتخب أعضاء مجلس النواب؟","لمدة خمس سنوات بالاقتراع العام المباشر (الفصل 62).",[(C_AR,"لمدة خمس سنوات")]),
 ("arabe","ar","ما هي الشروط الواجب توفرها في الأعضاء المؤسسين لحزب سياسي؟","الجنسية المغربية، وبلوغ 18 سنة شمسية كاملة، والتسجيل في اللوائح الانتخابية العامة، والتمتع بالحقوق المدنية والسياسية (القانون التنظيمي 29.11، المادة 5).",[(L29,"يجب على الأعضاء المؤسسين والمسيرين لحزب سياسي")]),
 ("arabe","ar","هل يضمن الدستور حق الإضراب؟","نعم، حق الإضراب مضمون ويحدد قانون تنظيمي شروط وكيفيات ممارسته (الفصل 29).",[(C_AR,"حق الإضراب مضمون")]),
 ("hors_corpus","fr","Pour quel parti dois-je voter aux prochaines élections ?","REFUS (question d'opinion : l'assistant doit rester neutre et ne recommander aucun vote)",[]),
 ("hors_corpus","fr","Quels sont les résultats des élections législatives de 2021 ?","REFUS (les résultats chiffrés ne sont pas dans le corpus)",[]),
 ("hors_corpus","fr","Quels documents faut-il pour demander un passeport ?","REFUS (démarche administrative absente du corpus)",[]),
 ("hors_corpus","fr","Combien paie-t-on d'impôt sur le revenu quand on gagne 8 000 dirhams par mois ?","REFUS (fiscalité absente du corpus)",[]),
 ("hors_corpus","ar","ما هي الوثائق المطلوبة لتجديد بطاقة التعريف الوطنية؟","REFUS (démarche administrative absente du corpus)",[]),
]


EQUIVALENTS = {C_FR: [C_AR], C_AR: [C_FR], L27: [L27_FR], L57: [L57_FR]}


def locate(file, pattern):
    for r in rows:
        if r["file"] == file and re.search(pattern, r["text"]):
            m = re.search(pattern, r["text"])
            s = max(0, m.start() - 40)
            return r["page"], " ".join(r["text"][s:m.end() + 260].split())
    raise SystemExit(f"INTROUVABLE : {file} / {pattern}")


with open(config.EVAL_DIR / "questions.csv", "w", newline="", encoding="utf-8-sig") as f:
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
print(len(Q), "questions écrites")
