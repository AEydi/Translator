import genanki
import os
import re
import platform
import wordsHaveDot


def readIconsColorFromTextFile():
    try:
        fileRead = open("color.txt", "r")
        color = fileRead.read()
        fileRead.close()
    except (Exception,):
        color = 'd'
        try:
            fileWrite = open('color.txt', "w")
            fileWrite.write('d')
            fileWrite.close()
        except (Exception,):
            pass
    return color


def createAnkiCardsModel():
    CardModel = genanki.Model(
        1380120064,
        'pyNote',
        fields=[
            {'name': 'Front'},
            {'name': 'Back'},
            {'name': 'MyMedia'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '{{Front}}{{MyMedia}}',
                'afmt': '{{FrontSide}}<hr id="answer">{{Back}}',
            },
        ],
        css='''
            .card {
            font-family: IRANSansWeb Medium;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
            }
            .card.night_mode {
            font-family: IRANSansWeb Medium;
            font-size: 20px;
            text-align: center;
            color: white;
            background-color: black;
            }
        ''')
    return CardModel


def myDeckName():
    try:
        fileRead = open("deckName.txt", "r")
        myDeckName = fileRead.read()
        fileRead.close()
    except Exception:
        myDeckName = 'IMPORTED'
        try:
            fileWrite = open('deckName.txt', "w")
            fileWrite.write('IMPORTED')
            fileWrite.close()
        except (Exception,):
            pass
    return myDeckName


def createExportFolder():
    if platform.system() == 'Windows':
        exportFolderPath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
    else:
        exportFolderPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop/Export')

    if not os.path.exists(exportFolderPath):
        os.mkdir(exportFolderPath)
    return exportFolderPath


def isTextURL(text):
    return re.search(r'((^(https|ftp|http):\/\/)|(^www.\w+\.)|(^))(\w+\.)(com|io|org|net|ir|edu|info|ac.(\w{2,'
                     r'3}))($|\/)', text) is None


def isTextPassword(text):
    return ((text.count(' ') > 2) | ((not any(c in text for c in ['@', '#', '$', '&'])) & (False if False in [
        False if (len(re.findall('([0-9])', t)) > 0) & (len(re.findall('([0-9])', t)) != len(t)) else True for t in
        text.split(' ')] else True)))


def wordContainDot(word):
    return '.' in word


def wordContainWordHaveDot(k, word):
    lineStart = "(^[^\w]|^|\n)"
    return re.search(r"" + lineStart + wordsHaveDot.words[k].replace(".", "\.") + "", word)


def inTextEmpty(word):
    return bool(word.strip())
