import csv

with open('input.txt', 'r', encoding='utf8') as i,  open('output.csv', 'w', newline='', encoding='utf8') as o:
    output = csv.writer(o)
    Buku,Bab,Bagian,Paragraf,Pasal,Ayat = '', '', '', '', '', ''
    output.writerow('Buku,Bab,Bagian,Paragraf,Pasal,Ayat'.split(','))
    for l in i.readlines():
        line = l.strip()
        if line == '':
            continue
        if line.startswith('BUKU '):
            Buku = line
        elif line.startswith('BAB '):
            Bab = line
        elif line.startswith('Bagian '):
            Bagian = line
        elif line.startswith('Paragraf '):
            Paragraf = line
        elif line.startswith('Pasal '):
            Pasal = line
        else:
            Ayat = line
            output.writerow([Buku,Bab,Bagian,Paragraf,Pasal,Ayat])
