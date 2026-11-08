"""Génère evaluation/questions_set2.csv : un deuxième jeu de 45 questions qui couvre presque tout le corpus.

    python -m evaluation.build_questions_set2

Pourquoi : les 30 premières questions ne visaient que 11 documents sur 35 (19 sur 25 visaient la Constitution).
Ce deuxième jeu vise chacun des 24 autres documents au moins une fois.

Règles suivies, pour que ce soit un vrai jeu de TEST :
  - les questions et les réponses attendues ont été écrites à partir des textes, AVANT de voir la moindre
    réponse du système ;
  - ce jeu n'est jamais utilisé pour régler le système (seuil, nombre de passages, consignes...) : on le
    lance, on publie les chiffres tels quels.

Comme pour le premier jeu, le script RETROUVE chaque passage dans les chunks (par une expression de
recherche) et recopie la page et l'extrait : aucune page ni extrait n'est écrit à la main.
"""

import csv
import json
import re
import sys

from src import config

sys.stdout.reconfigure(encoding="utf-8")
rows = [json.loads(line) for line in open(config.CHUNKS_FILE, encoding="utf-8")]

C_FR, C_AR = "constitution_2011_fr.pdf", "constitution_2011_ar.pdf"
L28 = "elections_loi_organique_28_11_chambre_conseillers_ar.pdf"
L55 = "elections_loi_55_25_modifiant_57_11_ar.pdf"
A503 = "elections_arrete_503_26_site_listes_electorales_ar.pdf"
L59 = "elections_loi_organique_59_11_collectivites_ar.pdf"
L64 = "participation_loi_organique_64_14_motions_ar.pdf"
L97 = "participation_loi_organique_97_15_greve_ar.pdf"
L26 = "participation_loi_organique_26_16_amazigh_ar.pdf"
L31 = "participation_loi_31_13_acces_information_fr.pdf"
L76 = "participation_loi_76_15_cndh_fr.pdf"
L79 = "participation_loi_79_14_autorite_parite_fr.pdf"
L88 = "participation_loi_88_13_presse_edition_fr.pdf"
L89 = "participation_loi_89_15_conseil_jeunesse_fr.pdf"
GUIDE = "participation_guide_parlement_gouvernement_ouvert_fr.pdf"
DECRET = "partis_decret_financement_distribution_ar.pdf"
RI = "institutions_reglement_interieur_chambre_representants_fr.pdf"
L130 = "institutions_loi_organique_130_13_loi_de_finances_fr.pdf"
L66 = "institutions_loi_organique_066_13_cour_constitutionnelle_fr.pdf"
L65 = "institutions_loi_organique_065_13_gouvernement_fr.pdf"
L85 = "institutions_loi_organique_085_13_commissions_enquete_fr.pdf"
L113 = "institutions_loi_organique_113_14_communes_ar.pdf"
L111 = "institutions_loi_organique_111_14_regions_ar.pdf"
L128 = "institutions_loi_organique_128_12_cese_fr.pdf"
L46 = "institutions_loi_46_19_instance_probite_fr.pdf"
L14 = "institutions_loi_14_16_mediateur_fr.pdf"

# Motifs de recherche (un espace dans le motif accepte n'importe quelle suite d'espaces ou de retours à la ligne)
P_28 = "يتألف مجلس المستشارين من"
P_64 = "لجنة تقديم الملتمس : لجنة مكونة من خمسة أعضاء"
P_55 = "تعتمد البطاقة الوطنية للتعريف وحدها للقيد"
P_503 = r"www\.listeselectorales\.ma"
P_269 = "Aucun Représentant ne peut signer plus d.une mention de censure"
P_271 = "fixe la date de la discussion de la motion de censure"
P_130 = "Article 48 Le projet de loi de finances de l.année est déposé"
P_GUIDE = "transparence, participation, responsabilité et inclusion"
P_DECRET = r"حصة تبلغ\s*50 في المائة"
P_59 = "ينتخب لمدة ست سنوات أعضاء مجالس الجهات"
P_66 = "prêtent serment devant le Roi"
P_65 = "propose au Roi de charger l.un des membres du gouvernement d.assurer son intérim"
P_85 = "Le rapport de la commission doit être déposé dans un délai maximum de six mois"
P_113 = "ثلاث دورات عادية في السنة خلال أشهر فبراير"
P_111 = "ثلاث دورات عادية في السنة خلال أشهر مارس"
P_128 = "de 105 membres répartis en cinq catégories"
P_128_MANDAT = r"le mandat de membre du Conseil est de cinq ans, renouvelable une seule fois"
P_46 = "L.Instance est une institution nationale indépendante dotée de la personnalité morale"
P_14 = r"Le Médiateur est nommé par dahir pour une période de cinq \(5\) ans, renouvelable une seule fois"
P_31 = r"dans un délai ne dépassant pas vingt \(20\) jours ouvrables"
P_97 = "الإضراب هو توقف مؤقت عن أداء العمل"
P_76 = "Le Conseil peut émettre des recommandations relatives aux plaintes dont il est saisi"
P_89 = "exerce, en tant qu.instance constitutionnelle consultative, les attributions suivantes"
P_79 = "recevoir et examiner les réclamations concernant les cas de discrimination"
P_88 = "Le directeur de publication doit remplir les conditions suivantes"
P_26 = "ويعتمد حرف تيفيناغ"
P_C62 = "élus pour cinq ans"
P_C67 = "peuvent être créées à l.initiative du Roi ou à la demande du tiers des membres de la Chambre des Représentants"

# (type, langue, question, réponse attendue, [(fichier, motif), ...])
# « simple » = une question en français sur un seul texte ; « arabe » = question en arabe ; « combinee » = deux textes.
Q = [
 # --- 24 documents jamais interrogés par le premier jeu, une question en français chacun
 ("simple", "fr", "Quelles catégories de représentants siègent à la Chambre des conseillers ?",
  "120 membres : 72 représentants des collectivités territoriales, 20 des chambres professionnelles, 8 des organisations professionnelles des employeurs les plus représentatives et 20 élus par un collège de représentants des salariés (loi organique 28-11).", [(L28, P_28)]),
 ("simple", "fr", "Combien de personnes faut-il au minimum pour former le comité qui présente une motion législative ?",
  "Au moins cinq membres, choisis par les initiateurs parmi eux, qui doivent appartenir à au moins un tiers des régions du Royaume (loi organique 64-14, art. 2).", [(L64, P_64)]),
 ("simple", "fr", "Quel document suffit désormais pour s'inscrire sur les listes électorales ?",
  "La carte nationale d'identité seule est retenue pour l'inscription (art. 3 de la loi 57-11, tel que modifié par la loi 55-25).", [(L55, P_55)]),
 ("simple", "fr", "Quelle est l'adresse du site officiel pour demander son inscription sur les listes électorales ?",
  "www.listeselectorales.ma, site du ministère de l'Intérieur, qui permet de demander son inscription ou le transfert de son inscription et de consulter ses données (arrêté 503-26).", [(A503, P_503)]),
 ("simple", "fr", "Un député peut-il signer plusieurs motions de censure à la fois ?",
  "Non : aucun représentant ne peut signer plus d'une motion de censure à la fois, et aucune signature ne peut être ajoutée ou retirée après le dépôt (règlement intérieur, art. 269).", [(RI, P_269)]),
 ("simple", "fr", "Avant quelle date le gouvernement doit-il déposer le projet de loi de finances ?",
  "Au plus tard le 20 octobre de l'année budgétaire en cours, sur le bureau de la Chambre des représentants (loi organique 130-13, art. 48).", [(L130, P_130)]),
 ("simple", "fr", "Quelles valeurs fondamentales le gouvernement ouvert met-il en avant pour les parlementaires ?",
  "La transparence, la participation, la responsabilité et l'inclusion (guide pratique du Partenariat pour un gouvernement ouvert).", [(GUIDE, P_GUIDE)]),
 ("simple", "fr", "Comment le soutien public aux partis politiques est-il réparti entre la gestion, les congrès et les études ?",
  "50 % pour la gestion des partis, 30 % pour les congrès nationaux ordinaires et 20 % en soutien annuel supplémentaire pour les missions, études et recherches (décret 2.12.293 modifié en 2022, art. 1).", [(DECRET, P_DECRET)]),
 ("simple", "fr", "Pour combien d'années sont élus les conseillers communaux et régionaux ?",
  "Pour six ans (loi organique 59-11, art. 2).", [(L59, P_59)]),
 ("simple", "fr", "Devant qui les membres de la Cour constitutionnelle prêtent-ils serment ?",
  "Devant le Roi, avant d'entrer en fonction (loi organique 066-13, art. 4).", [(L66, P_66)]),
 ("simple", "fr", "Qui remplace le Chef du gouvernement quand il est absent ?",
  "Le Chef du gouvernement propose au Roi de charger un membre du gouvernement d'assurer son intérim, pour un délai limité et pour des fonctions déterminées ; l'intérim cesse dès qu'il reprend ses fonctions (loi organique 065-13, art. 8).", [(L65, P_65)]),
 ("simple", "fr", "Dans quel délai une commission d'enquête parlementaire doit-elle remettre son rapport ?",
  "Six mois au maximum, éventuellement prorogés du temps nécessaire à la Cour constitutionnelle pour statuer ; sans rapport dans ce délai, la commission est dissoute (loi organique 085-13).", [(L85, P_85)]),
 ("simple", "fr", "Combien de sessions ordinaires le conseil communal tient-il par an, et à quelle période ?",
  "Trois sessions ordinaires par an, en février, mai et octobre (loi organique 113-14, art. 33).", [(L113, P_113)]),
 ("simple", "fr", "Combien de membres compte le Conseil économique, social et environnemental ?",
  "105 membres, en plus de son président nommé par dahir, répartis en cinq catégories (loi organique 128-12, art. 11).", [(L128, P_128)]),
 ("simple", "fr", "L'instance chargée de lutter contre la corruption est-elle indépendante, et où siège-t-elle ?",
  "Oui : c'est une institution nationale indépendante, dotée de la personnalité morale et de l'autonomie financière et administrative ; son siège est à Rabat (loi 46-19, art. 2).", [(L46, P_46)]),
 ("simple", "fr", "Pour combien de temps le Médiateur est-il nommé ?",
  "Cinq ans, renouvelables une seule fois ; il est nommé par dahir (loi 14-16, art. 4).", [(L14, P_14)]),
 ("simple", "fr", "En combien de temps une administration doit-elle répondre à une demande d'accès à l'information ?",
  "Dans un délai maximum de 20 jours ouvrables à compter de la réception de la demande, prolongeable d'une durée similaire dans certains cas ; 3 jours en cas d'urgence pour protéger la vie, la sécurité ou la liberté des personnes (loi 31-13, art. 16 et 17).", [(L31, P_31)]),
 ("simple", "fr", "Comment la loi définit-elle la grève ?",
  "Un arrêt temporaire, total ou partiel, du travail, décidé par la partie qui appelle à la grève et exercé par un groupe de salariés ou de professionnels pour défendre un droit ou un intérêt social, économique, professionnel ou moral lié aux conditions de travail et à l'exercice de la profession (loi organique 97-15, art. 2).", [(L97, P_97)]),
 ("simple", "fr", "Que peut faire le Conseil national des droits de l'Homme quand il reçoit une plainte ?",
  "Il peut émettre des recommandations à l'autorité concernée et en suivre l'application, et saisir le ministère public si les faits relèvent d'actes pénalement incriminés (loi 76-15, art. 8).", [(L76, P_76)]),
 ("simple", "fr", "À quoi sert le Conseil consultatif de la jeunesse et de l'action associative ?",
  "C'est une instance constitutionnelle consultative (art. 33 de la Constitution) : elle donne son avis sur les questions de jeunesse et d'action associative, élabore une charte d'éthique de l'action associative et émet des recommandations pour promouvoir la condition des jeunes et l'action associative (loi 89-15, art. 2).", [(L89, P_89)]),
 ("simple", "fr", "Où peut-on déposer une réclamation pour un cas de discrimination ?",
  "Auprès de l'Autorité pour la parité et la lutte contre toutes formes de discrimination, qui reçoit et examine les réclamations de toute personne s'estimant victime et formule des recommandations aux autorités compétentes (loi 79-14, art. 2).", [(L79, P_79)]),
 ("simple", "fr", "Quelles conditions faut-il remplir pour être directeur de publication d'un journal ?",
  "Être majeur, de nationalité marocaine et domicilié au Maroc ; avoir au moins une licence ou un diplôme spécialisé en presse ; jouir de ses droits civils ; ne pas avoir été condamné définitivement pour certaines infractions (chantage, escroquerie, corruption...) ; avoir le statut de journaliste professionnel (loi 88-13, art. 16).", [(L88, P_88)]),
 ("simple", "fr", "Quel alphabet est utilisé pour écrire la langue amazighe ?",
  "L'alphabet tifinagh (loi organique 26-16, art. 1).", [(L26, P_26)]),
 # --- un deuxième angle sur le règlement intérieur (212 pages)
 ("simple", "fr", "Dans quel délai la Chambre discute-t-elle une motion de censure après son dépôt ?",
  "Au plus tard sept jours à compter du dépôt de la motion auprès du Président de la Chambre (règlement intérieur, art. 271).", [(RI, P_271)]),
 # --- sept questions en arabe (4 sur des textes en arabe, 3 sur des textes en français)
 ("arabe", "ar", "ما هي مدة تعيين الوسيط؟",
  "خمس سنوات قابلة للتجديد مرة واحدة، ويعين بظهير (القانون 14.16، المادة 4).", [(L14, P_14)]),
 ("arabe", "ar", "ما هي المدة التي يجب على الإدارة أن تجيب خلالها عن طلب الحصول على المعلومات؟",
  "عشرون يوم عمل كحد أقصى من تاريخ التوصل بالطلب، قابلة للتمديد بمدة مماثلة، وثلاثة أيام في حالات الاستعجال (القانون 31.13، المادتان 16 و17).", [(L31, P_31)]),
 ("arabe", "ar", "كم عدد أعضاء المجلس الاقتصادي والاجتماعي والبيئي؟",
  "105 أعضاء، إضافة إلى رئيسه المعين بظهير، موزعون على خمس فئات (القانون التنظيمي 128.12، المادة 11).", [(L128, P_128)]),
 ("arabe", "ar", "كيف يعرف القانون الإضراب؟",
  "توقف مؤقت عن أداء العمل كليا أو جزئيا، يتخذ بقرار من الجهة الداعية إلى الإضراب ويمارسه مجموعة من العمال أو المهنيين للدفاع عن حق أو مصلحة اجتماعية أو اقتصادية أو مهنية أو معنوية (القانون التنظيمي 97.15، المادة 2).", [(L97, P_97)]),
 ("arabe", "ar", "كم عدد أعضاء لجنة تقديم الملتمس في مجال التشريع على الأقل؟",
  "خمسة أعضاء على الأقل، ينتسبون إلى ثلث عدد جهات المملكة على الأقل (القانون التنظيمي 64.14، المادة 2).", [(L64, P_64)]),
 ("arabe", "ar", "كيف يتوزع أعضاء مجلس المستشارين؟",
  "120 عضوا: 72 يمثلون الجماعات الترابية، و20 الغرف المهنية، و8 المنظمات المهنية للمشغلين، و20 ممثلين للمأجورين (القانون التنظيمي 28.11).", [(L28, P_28)]),
 ("arabe", "ar", "في أي أشهر يعقد مجلس الجهة دوراته العادية؟",
  "ثلاث دورات عادية في السنة خلال أشهر مارس ويوليو وأكتوبر (القانون التنظيمي 111.14، المادة 36).", [(L111, P_111)]),
 # --- quatre questions qui demandent deux textes
 ("combinee", "fr", "Pour combien de temps sont élus les députés et les conseillers communaux ?",
  "Les députés pour cinq ans (Constitution, art. 62) ; les conseillers communaux, provinciaux et régionaux pour six ans (loi organique 59-11, art. 2).", [(C_FR, P_C62), (L59, P_59)]),
 ("combinee", "fr", "Combien de temps dure le mandat du Médiateur et celui d'un membre du Conseil économique, social et environnemental ?",
  "Cinq ans, renouvelables une seule fois, dans les deux cas (loi 14-16, art. 4 ; loi organique 128-12, art. 14, hors catégorie des personnalités représentant des institutions et organismes).", [(L14, P_14), (L128, P_128_MANDAT)]),
 ("combinee", "fr", "À quelles périodes se réunissent le conseil communal et le conseil régional ?",
  "Le conseil communal en février, mai et octobre (loi organique 113-14, art. 33) ; le conseil régional en mars, juillet et octobre (loi organique 111-14, art. 36).", [(L113, P_113), (L111, P_111)]),
 ("combinee", "fr", "Qui peut demander la création d'une commission d'enquête, et dans quel délai doit-elle remettre son rapport ?",
  "Le Roi, ou le tiers des membres de l'une des deux Chambres (Constitution, art. 67) ; six mois au maximum (loi organique 085-13).", [(C_FR, P_C67), (L85, P_85)]),
 # --- dix questions hors corpus (écrites sans regarder les scores de recherche)
 ("hors_corpus", "fr", "Quel est le salaire minimum au Maroc ?", "REFUS (le salaire minimum n'est fixé par aucun texte du corpus)", []),
 ("hors_corpus", "fr", "Comment obtenir un visa pour la France depuis le Maroc ?", "REFUS (démarche étrangère absente du corpus)", []),
 ("hors_corpus", "fr", "Comment créer une société à responsabilité limitée au Maroc ?", "REFUS (droit des sociétés absent du corpus)", []),
 ("hors_corpus", "fr", "À partir de quel âge peut-on passer le permis de conduire ?", "REFUS (code de la route absent du corpus)", []),
 ("hors_corpus", "fr", "Quel est le nom du ministre de l'Éducation nationale en ce moment ?", "REFUS (les titulaires actuels des fonctions ne figurent pas dans les textes)", []),
 ("hors_corpus", "fr", "Quels sont les horaires d'ouverture de la mairie de Casablanca ?", "REFUS (information pratique absente du corpus)", []),
 ("hors_corpus", "fr", "Comment faire une demande de naturalisation marocaine ?", "REFUS (code de la nationalité absent du corpus)", []),
 ("hors_corpus", "fr", "Le gouvernement actuel fait-il du bon travail ?", "REFUS (question d'opinion : l'assistant doit rester neutre)", []),
 ("hors_corpus", "ar", "ما هي شروط الحصول على جواز السفر؟", "REFUS (démarche administrative absente du corpus)", []),
 ("hors_corpus", "ar", "ما هو سعر صرف الدرهم مقابل الدولار؟", "REFUS (information financière absente du corpus)", []),
]

EQUIVALENTS = {C_FR: [C_AR], C_AR: [C_FR]}   # même texte dans l'autre langue : l'une OU l'autre version suffit


def locate(file, pattern):
    regex = re.compile(pattern.replace(" ", r"\s+"))
    for r in rows:
        if r["file"] == file:
            m = regex.search(r["text"])
            if m:
                s = max(0, m.start() - 40)
                return r["page"], " ".join(r["text"][s : m.end() + 260].split())
    raise SystemExit(f"INTROUVABLE : {file} / {pattern}")


def main() -> None:
    with open(config.EVAL_DIR / "questions_set2.csv", "w", newline="", encoding="utf-8-sig") as f:
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
    documents = {file for q in in_corpus for file, _ in q[4]}
    print(f"{len(Q)} questions écrites : {len(in_corpus)} sur le corpus, {len(Q) - len(in_corpus)} hors corpus")
    print(f"documents visés par ce jeu : {len(documents)}")


if __name__ == "__main__":
    main()
