"""Regenerate the kb-v2 C3 PDF fixtures (small stand-ins for scraped PDFs).

    python app/tests/fixtures/scraping/c3/make_pdfs.py

Real scraped PDFs are 150 KB to 2 MB, so the tests use these: a sectioned
KP Act, an Act with no sections, garbled text, an image-only scan, a core
law (Contract Act), and a Federal Shariat Court judgment.
"""

from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent

ACT = """THE KHYBER PAKHTUNKHWA TRADE TESTING BOARD ACT, 2025.
(KHYBER PAKHTUNKHWA ACT NO. IV OF 2025)
AN
ACT
to establish a Trade Testing Board in the Province of the Khyber Pakhtunkhwa.
WHEREAS it is expedient to establish a Board for testing and certification of trades;
It is hereby enacted as follows:
1. Short title, extent and commencement.-- (1) This Act may be called the Khyber Pakhtunkhwa
Trade Testing Board Act, 2025. (2) It extends to the whole of the Province of the Khyber
Pakhtunkhwa. (3) It shall come into force at once.
2. Definitions.-- In this Act, unless the context otherwise requires, (a) "Board" means the
Trade Testing Board established under section 3; (b) "Government" means the Government of the
Khyber Pakhtunkhwa; (c) "prescribed" means prescribed by rules made under this Act.
3. Establishment of the Board.-- (1) As soon as may be after the commencement of this Act, the
Government shall, by notification in the official Gazette, establish a Board to be known as the
Trade Testing Board. (2) The Board shall be a body corporate having perpetual succession.
4. Functions of the Board.-- The Board shall conduct trade tests, award certificates to persons
who pass them, and maintain a register of certified tradesmen in the prescribed manner.
5. Power to make rules.-- Government may, by notification in the official Gazette, make rules
for carrying out the purposes of this Act. 1Subs. by the Khyber Pakhtunkhwa Finance Act, 2025.
"""

NO_SECTIONS = """THE KHYBER PAKHTUNKHWA NOTICE ON PARKS, 2025
This notice informs the public that the parks of the province will remain open during the
holidays and that visitors are requested to keep them clean. The department thanks the public
for its cooperation and hopes that families will enjoy the gardens, the walking tracks and the
play areas that have been renovated during the year with the help of local volunteers and the
municipal committees of each district of the province.
"""

GARBLED = "THE ACT, 2025\n" + "\n".join("~ # 4 ^ % 7 | = 3 ; + 9 ) ( 2 & 8 * 1 @ 6 ! 5 $ 0 . , : / - _ \\ < > { } [ ] ' \"" for _ in range(20))

CONTRACT = """THE CONTRACT ACT, 1872
(ACT NO. IX OF 1872)
1. Short title.-- This Act may be called the Contract Act, 1872. It extends to the whole of Pakistan.
2. Interpretation clause.-- In this Act the following words and expressions are used in the
following senses, unless a contrary intention appears from the context.
3. Communication of proposals.-- The communication of proposals, the acceptance of proposals,
and the revocation of proposals and acceptances, respectively, are deemed to be made by any act.
"""

JUDGMENT = """IN THE FEDERAL SHARIAT COURT
(Original Jurisdiction)
PRESENT
MR. JUSTICE DR. SYED MUHAMMAD ANWER
MR. JUSTICE KHADIM HUSSAIN M. SHAIKH
SHARIAT PETITION NO. 16/I OF 2022
Haji Saif ur Rehman ... PETITIONER
Versus
Federation of Pakistan through Secretary Ministry of Law ... RESPONDENTS
Date of hearing: 06.10.2023
JUDGMENT
""" + "\n".join(
    f"{n}. The question before the Court is whether the provisions concerning khula and the dissolution of "
    f"marriage are repugnant to the injunctions of Islam. The petitioner argues that the wife may seek "
    f"khula only with the consent of the husband, and the Court has examined the Holy Quran and Sunnah on "
    f"the point at length in paragraph {n} of this judgment."
    for n in range(1, 9))


def pdf(text: str) -> bytes:
    doc = pymupdf.open()
    lines = text.splitlines()
    for i in range(0, len(lines), 40):
        page = doc.new_page()
        page.insert_textbox(pymupdf.Rect(40, 40, 560, 800), "\n".join(lines[i:i + 40]), fontsize=8)
    data = doc.tobytes()
    doc.close()
    return data


def scan() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 50, 50), False)
    pix.clear_with(200)
    page.insert_image(page.rect, pixmap=pix)
    data = doc.tobytes()
    doc.close()
    return data


if __name__ == "__main__":
    for name, data in {"act.pdf": pdf(ACT), "no_sections.pdf": pdf(NO_SECTIONS), "garbled.pdf": pdf(GARBLED),
                       "contract_act.pdf": pdf(CONTRACT), "judgment.pdf": pdf(JUDGMENT), "scan.pdf": scan()}.items():
        (HERE / name).write_bytes(data)
        print(name, len(data))
