from spellchecker import SpellChecker
for s in ['en','de','fr']:
    spell = SpellChecker(language= s, distance=1)
    word = 'corre'
    r = []
    if len(spell.known({word})) == 0:
        words = list(spell.candidates(word))
        res = {words[i]: spell.word_probability(words[i]) for i in range(len(words))}
        d = sorted(res.items(), key=lambda item: item[1], reverse=True)

        for i in range(min(6,len(d))):
            r.append(d[i][0])
    print(r)