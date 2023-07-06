from bs4 import BeautifulSoup
from requests import get
from PIL import Image, ImageDraw, ImageFont
import aiohttp

from CONSTANTS import ROOT_PATH


def source_text_pattern(_text: str) -> str:
    """
    This function handles the text (source of hadith) for more readable view.
    :param _text: source text of hadith
    :return: handled readable text
    """

    # find word and get word's index in text
    end_idx = _text.find(' См.')

    # cut off the part of the text after found word
    _text = _text[:end_idx]

    # replace abbreviations for more readable view
    _text = _text.replace("св. х.", "Свод хадисов").replace("Св. х.", "Свод хадисов")
    _text = _text.replace("; ", ";\n").strip()

    return _text


def get_dua_or_hadith_text(_url: str, _type="") -> tuple:
    """
    This function gets and handles dua, ayah or hadith text from given url.
    :param _url: URL of page in `umma.ru` site with current dua, ayah or hadith
    :param _type: type of current content: ayah, dua or hadith
    :return: for ayah: pointer in Qur'an, arabic translation, russian translation;
    for dua: arabic text of dua, transcription and russian translation;
    for hadith: source, hadith text.
    """
    response = get(_url)

    soup = BeautifulSoup(response.text, 'html.parser')

    # remove footnote links from text (like [1], [2]...)
    for i in soup.select('article p a'):
        # here are could be ayah pointer as a link, so we should check it
        if "св. коран" not in i.text.lower():
            i.extract()

    if _type == "hadith":
        # the main text of hadith
        body_text = soup.select('article p:first-child')[0].text

        # the text of source of hadith
        source = soup.select('article p:last-child')[-1].text

        readable_source = source_text_pattern(source)

        if readable_source:
            return readable_source, body_text

    elif _type == "ayah":
        # the main text of ayah. all paragraphs except the last one (because it is just link to 'Dzen')
        body_text = ' '.join([el.text for el in soup.select('article p')])
        if not body_text:
            body_text = soup.select('article div')[0].text

        # cut off part of the text after "Св. Коран...)." words
        body_text = body_text[: body_text.find(
            ")",
            body_text.find("Св. Коран, ") + 11
        ) + 2]

        # surah and ayah number in Quran (ex.: 3:7). it is between "Св. Коран," and ")." words
        ayah_pointer = body_text[body_text.find("Св. Коран, ") + 11: body_text.find(
            ")",
            body_text.find("Св. Коран, ") + 11
        )]

        # it is possible that there is few ayahs, not only one. so we get all ayahs numbers separated with `, `
        surah_num = ayah_pointer.split(":")[0]
        ayah_nums_in_surah = ayah_pointer.split(":")[-1].split(", ")

        # ayah arabic translation
        ayah_arabic = ""
        for ayah_num in ayah_nums_in_surah:
            # ayah arabic translation
            ayah_arabic += get_ayah_arabic_translate(surah_num + ":" + ayah_num)
            ayah_arabic += '\n'

        body_text = ayah_arabic + '\n' + body_text

        return ayah_pointer, body_text

    else:
        # remove 'Dzen' link
        for i in soup.select('article div'):
            i.extract()

        # get header or dua in site
        header = soup.find(class_="upage__title").text.strip()

        # the main text of dua.
        body_text = '\n'.join(
            ['' if 'Смотрите другие дуа на разные случаи' in el.text else el.text for el in soup.select('article p')])
        # make text more readable by replacing abbreviations
        body_text = body_text.replace("св. х.", "Свод хадисов").replace("Св. х.", "Свод хадисов")
        # remove excess blank lines
        body_text = body_text.strip()

    return header, body_text


def get_ayah_arabic_translate(pointer: str) -> str:
    """
    This function gets arabic text of ayah by its pointer in Qur'an.
    :param pointer: surah no. and ayah no. (for example: 3:31)
    :return: ayah in arabic
    """
    url = "https://quran-online.ru/" + pointer

    response = get(url)

    soup = BeautifulSoup(response.text, 'html.parser')

    try:
        surah_text = soup.find("span", class_="original-text original-text-rtl").text
    except AttributeError:
        return ''
    return surah_text


def get_link_of_ayah_or_hadith_of_the_day(_type="") -> str:
    """
    This function returns the link of ayah or hadith of the day from `umma.ru` site
    :param _type: type of content: 'ayah' or 'hadith'
    :return: URL for ayah or hadith of the day
    """
    url = "https://umma.ru"
    response = get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # here we will save url for hadith and ayah of the day
    links = {}

    # links are inside <div> tag with such class
    for i in soup.find_all(class_="read-more"):
        # get URL from <a> tag
        content_url = url + i.a.get('href')

        if 'aya' in content_url:
            links["ayah"] = content_url
        else:
            links["hadith"] = content_url

    if _type == "ayah":
        return links["ayah"]
    return links["hadith"]


def prettify_text(text, _type=""):
    """
    This function prettifies given (remodels to a template for telegram) text depending on
    the type of content.
    :param text: content text
    :param _type: the type of content: dua, hadith or ayah
    :return:
    """
    pretty_text = ""

    if _type == "ayah":
        pointer, content = text
        pretty_text += f"💬 *Аят дня. {pointer}*\n\n"
        pretty_text += content + "\n\n"

    elif _type == "hadith":
        source, content = text
        pretty_text += "📖 *Хадис дня*\n"
        pretty_text += f"📚 *{source}*\n\n"
        pretty_text += content + "\n\n"

    else:
        header, content = text

        pretty_text += f"🤲 *{header}*\n\n"

        # put some words into bold font
        content = content.replace("Транскрипция дуа:", "\n*Транскрипция:*").replace(
            "Перевод дуа:", "\n*Перевод: *").replace("Транскрипция:", "\n*Транскрипция:*").replace(
            "Перевод:", "\n*Перевод: *")

        pretty_text += content + "\n\n"

    pretty_text += "©️*Твой Проповедник*"

    return pretty_text


def set_ayah_pointer_in_img(pointer: str) -> None:
    """
    This function adds pointer of ayah on image of ayah of the day
    :param pointer: pointer or ayah in Qur'an (ex. 5:44)
    :return: None. Saves image in `img` directory.
    """

    # split surah num and ayah num
    surah, ayah = pointer.split(":")
    # save only first ayah's num if there is more than one
    ayah = ayah.split(", ")[0]

    # make text with surah num and ayah num on different rows
    text = surah + '\n' + ayah

    font = ImageFont.truetype(ROOT_PATH + "fonts/QANELAS-SEMIBOLD.TTF", size=40)

    with Image.open(ROOT_PATH + "img/ayah.png") as im:
        draw_text = ImageDraw.Draw(im)

        # draw our text with center of text block in (110, 110)
        draw_text.text(
            (110, 110),
            text,
            fill=('#020a00'),
            font=font,
            align="center",
            anchor='mm'
        )
        draw_text.text(
            (110, 98),
            "..",
            fill=('#020a00'),
            font=font,
            align="center",
            anchor='mm'
        )
        im.save(ROOT_PATH + "img/ayah_day.png")


async def get_all_duas_links() -> set:
    """
    This function gets URLs of all dua from site
    :return: urls in set()
    """
    dua = set()
    U = "https://umma.ru/dua-musulmanskie-molitvy/page/"

    async with aiohttp.ClientSession() as session:
        # there are 13 pages of duas on `umma.ru` site
        for i in range(1, 14):
            url = U + str(i)

            async with session.get(url) as response:
                soup = BeautifulSoup(await response.text(), 'html.parser')

                # get link of dua page from <a> tag
                for s in soup.select('article div h2 a'):
                    dua.add("https://umma.ru" + s.get("href"))

    return dua



# url = get_link_of_ayah_or_hadith_of_the_day(_type="ayah")
# print(url)
# tp = "ayah"
# print(prettify_text(
#     get_dua_or_hadith_text(
#         url,
#         _type=tp
#     ),
#     _type=tp))
# set_ayah_pointer_in_img("14:42")
