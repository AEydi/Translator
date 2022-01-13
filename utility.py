import genanki
import os
import re
import platform
import wordsHaveDot


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
                'afmt': "<div id='front'>{{FrontSide}}</div><hr id='answer'>{{Back}} "
                        "<script> "
                        "function checkRtl( character ) { "
                        "var RTL = ['ا','ب','پ','ت','س','ج','چ','ح','خ','د','ذ','ر','ز','ژ','س','ش','ص','ض','ط','ظ',"
                        "'ع','غ','ف','ق','ک','گ','ل','م','ن','و','ه','ی']; "
                        "    return RTL.indexOf( character ) > -1; "
                        "}; "
                        " "
                        "var divs = document.getElementsByTagName( 'div' ); "
                        " "
                        "for ( var index = 0; index < divs.length; index++ ) { "
                        "    if( checkRtl( divs[index].textContent[0] ) ) { "
                        "        divs[index].className = 'rtl'; "
                        "    } else { "
                        "        divs[index].className = 'ltr'; "
                        "    }; "
                        "}; "
                        " "
                        "document.getElementById('front').style.textAlign = 'center'; "
                        "</script>",
            },
        ],
        css='''
            .card {
                font-family: IRANSansWeb Medium;
                font-size: 20px;
                color: black;
                background-color: white;	
                text-align:center;
                }
                .card.night_mode {
                font-family: IRANSansWeb Medium;
                font-size: 20px;
                text-align:center;
                color: white;
                background-color: black;
                }
                        
            .rtl {
                direction: rtl;
                text-align: right;
                unicode-bidi: bidi-override;
                max-width:90%;
                margin: 0 auto;
                }
                @media (max-width: 600px) {
                    .rtl {
                    max-width:100%;
                    }}
            
            .ltr {
                direction: ltr; 
                text-align: left;
                unicode-bidi: bidi-override;
                max-width:90%;
                margin: 0 auto;
                }
                @media (max-width: 600px) {
                    .ltr {
                    max-width:100%;
                    }}
        ''')
    return CardModel


def createExportFolder():
    if platform.system() == 'Windows':
        exportFolderPath = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop\\Export')
    else:
        exportFolderPath = os.path.join(os.path.join(os.path.expanduser('~')), 'Desktop/Export')

    if not os.path.exists(exportFolderPath):
        os.mkdir(exportFolderPath)
    return exportFolderPath


def textIsURL(text):
    return re.search(r'((^(https|ftp|http):\/\/)|(^www.\w+\.)|(^))(\w+\.)(com|io|org|net|ir|edu|info|ac.(\w{2,'
                     r'3}))($|\/)', text) is None


def textIsPassword(text):
    return ((text.count(' ') > 2) | ((not any(c in text for c in ['@', '#', '$', '&'])) & (False if False in [
        False if (len(re.findall('([0-9])', t)) > 0) & (len(re.findall('([0-9])', t)) != len(t)) else True for t in
        text.split(' ')] else True)))


def wordContainDot(word):
    return '.' in word


def wordContainWordHaveDot(k, word):
    lineStart = "(^[^\w]|^|\n)"
    return re.search(r"" + lineStart + wordsHaveDot.words[k].replace(".", "\.") + "", word)


def textIsEmpty(word):
    return bool(word.strip())
