#!/usr/bin/env python
# encoding: utf-8

"""Skript na generování atlasu kodexových a jedovatých hub na mykologické zkoušky z myko.cz"""

# Copyright (c) 2023 Martin Malec
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import requests
from bs4 import BeautifulSoup
import urllib.parse
import os
from slugify import slugify
import re
import argparse
import datetime
import latexcodec

# Argument parser
parser = argparse.ArgumentParser(description="Skript na generování atlasu kodexových a jedovatých hub na mykologické zkoušky z myko.cz")
parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
args = parser.parse_args()
verbose = args.verbose

current_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
script_version = "v2023-06-05"
script_name = "Skript na generování atlasu kodexových a jedovatých hub na mykologické zkoušky z myko.cz"
script_author = "Martin Malec <martin@brozkeff.net> + ChatGPT. License: MIT"
disclaimer = "Dokument vytvořil "+ script_name + " (Autor "+ script_author + ", "+ script_version +"), bez záruky!"

print(script_name)
print(script_author)
print(script_version)

font_options = ["Source Sans Pro",
                "TeX Gyre Heros Cn",
                "FreeSans",
                "Ubuntu",
                "Roboto",
                "Roboto Condensed",
                "Linux Biolinum", 

                "FreeSerif",
                "Lido ST",
                "Lido STF Cond",
                "Linux Libertine",
                "Linux Libertine O"
                ]

print("\nVyber font, kterým atlas vysázet:")
for i, option in enumerate(font_options):
    print(f"{i+1}. {option}")

selected_index = input("Zadej číslo fontu který použít [1]: ")
if selected_index == "":
    selected_index = "1"

selected_index = int(selected_index) - 1

if selected_index < 0 or selected_index >= len(font_options):
    print("Invalid font selection.")
else:
    usedfont = font_options[selected_index]
    if verbose:
        print(f"Zvolen font '{usedfont}'")

# Výběr textu na titulní stranu jaký typ atlasu se generuje
options = [
    {
        'maintitle': 'Kodexové houby (Příloha 15 vyhl. 397/2021 Sb.)',
        'subtitle': 'Volně rostoucí houby',
        'subsubtitle': 'Texty a foto: myko.cz'
    },
    {
        'maintitle': 'Kodexové houby (Příloha 15 vyhl. 397/2021 Sb.)',
        'subtitle': 'Volně rostoucí houby určené pouze pro další průmyslové zpracování',
        'subsubtitle': 'Texty a foto: myko.cz'
    },
    {
        'maintitle': 'Jedovaté houby (Příloha 2 vyhl. 475/2002 Sb.)',
        'subtitle': 'Rozlišované jedovaté houby (§ 3 odst. 1)',
        'subsubtitle': 'Texty a foto: myko.cz'
    }
]

# Výběr soubor se seznamem hub a odkazy na myko.cz v DokuWiki formátu
# ve tvaru např.
#   - Čirůvka dvoubarvá - [[https://www.myko.cz/myko-atlas/Lepista-personata/|Lepista personata]]
print("Jaký seznam hub je připravený v mushrooms*.txt?")
for i, option in enumerate(options):
    print(f"{i + 1}. {option['maintitle']} - {option['subtitle']}")
selected_option = int(input("Vyber číslo volby: "))

if selected_option in range(1, len(options) + 1):
    selected_option -= 1
    maintitle = options[selected_option]['maintitle']
    subtitle = options[selected_option]['subtitle']
    subsubtitle = options[selected_option]['subsubtitle']

# Vytvoření pomocných složek pro jpg obrázky a jednotlivé .tex soubory
if not os.path.exists('images'):
    os.makedirs('images')
    if verbose:
        print("Vytvořena složka images/ pro jpg obrázky galerie hub.")

if not os.path.exists('tex'):
    os.makedirs('tex')
    if verbose:
        print("Vytvořena složka tex/ pro jednotlivé .tex soubory hub.")


# Zobrazení seznamu hub v souborech mushrooms*.txt
file_list = [filename for filename in os.listdir('.') if filename.startswith('mushrooms') and filename.endswith('.txt')]

print("\nDostupné soubory se seznamy hub:")
for i, filename in enumerate(file_list):
    print(f"{i+1}. {filename}")

default_file = 'mushrooms.txt' if 'mushrooms.txt' in file_list else None
user_input = input(f"Vyber který seznam hub použít (výchozí: {default_file}): ")

try:
    selected_index = int(user_input) - 1
    if selected_index >= 0 and selected_index < len(file_list):
        selected_file = file_list[selected_index]
    else:
        selected_file = default_file
except ValueError:
    selected_file = default_file

with open(selected_file, 'r') as f:
    lines = f.readlines()

user_input = input("\nStahovat znovu jednotlivé HTML z myko.cz (Y/N)?")
if user_input.lower() == 'y':
    for line in lines:
        name = re.search(r'\|(.*?)\]\]', line).group(1)
        url = re.search(r'\[\[(.*?)\|', line).group(1)
        print(f"Stahuji stránku {url} pro {name}.")
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        main_heading = soup.find('div', {'id': 'content'}).find('h2').text.encode('latex').decode('utf-8')
        try:
            sub_heading = soup.find('div', {'id': 'content'}).find('h2').find_next_sibling('p').text.encode('latex').decode('utf-8')
        except AttributeError:
            sub_heading = ''
        subsections = soup.find('div', {'id': 'content'}).find_all('h3')

        # Extrakce sekce Literatura
        literature_table = soup.find('div', {'id': 'content'}).find_all('table', {'class': 'atlas'})
        if literature_table:
            literature_table = literature_table[-1]
            literature_entries = literature_table.find_all('td', style=lambda value: value and 'vertical-align:baseline' in value)
        else:
            literature_entries = []

        # Extrakce sekce Systematika
        systematika_section = soup.find('div', {'id': 'content'}).find('h3', text='Systematika')
        if systematika_section:
            systematika_table = systematika_section.find_next_sibling('table')
            systematika_entries = systematika_table.find_all('a')
        else:
            systematika_entries = []

        # Extrakce sekce Synonyma
        synonyma_section = soup.find('div', {'id': 'content'}).find('h3', text='Synonyma')
        if synonyma_section:
            synonyma_p = synonyma_section.find_next_sibling('p')
            synonyma_entries = synonyma_p.text.split('\n')
        else:
            synonyma_entries = []

        # Extrakce seznamu JPG obrázků v plném rozlišení
        image_tables = soup.find_all('table', {'class': 'atlas'})
        image_urls = []
        for table in image_tables[1:]:
            images = table.find_all('img')
            for img in images:
                image_urls.append(img['src'])

        image_filenames = []
        for image_url in image_urls:
            # Replace the 's' in the filename with 'p' to get the full-res image
            full_res_url = urllib.parse.urljoin(url, image_url.replace('s.jpg', 'p.jpg'))
            filename = 'images/' + full_res_url.split('/')[-1]
            image_filenames.append(filename)

            # Zde případně doplnit další přípony co se nemají stahovat
            blacklisted_extensions = ['bmp']
            
            file_extension = full_res_url.split('.')[-1].lower()
            if file_extension in blacklisted_extensions:
                if verbose:
                    print(f"Přeskakuji stažení obrázku {full_res_url}, protože přípona je zakázaná.")
            else:
                if os.path.exists(filename):
                    if verbose:
                        print(f"Přeskakuji stažení obrázku {full_res_url}, protože soubor už existuje.")
                else:
                    if verbose:
                        print(f"Stahuji obrázek {full_res_url}.")
                    response = requests.get(full_res_url)
                    with open(filename, 'wb') as f:
                        f.write(response.content)

        # Vytvoření jednotlivého .tex souboru s fotogalerií a textem ke konkrétní houbě
        print(f"Převádím HTML stránku {name} do .tex formátu.")
        with open('tex/' + name.replace(' ', '_') + '.tex', 'w') as f:
            f.write('\\section{' + main_heading + '}\n')
            if sub_heading:
                f.write('\\subsection*{' + sub_heading + '}\n')
            f.write('\\begin{figure}[h]\n')
            f.write('\\centering\n')
            for filename in image_filenames:
                if not filename.endswith('.bmp'):
                    f.write('\\includegraphics[width=0.19\\textwidth]{' + filename + '}\n')
            f.write('\\end{figure}\n')
            f.write('\\small\n')

            if systematika_entries:
                f.write('\\subsubsection*{Systematika}\n')
                f.write("\\scriptsize\n")
                for i, entry in enumerate(systematika_entries):
                    if i != len(systematika_entries) - 1:
                        f.write(entry.text.encode('latex').decode('utf-8') + ' -- ')
                    else:
                        f.write(entry.text.encode('latex').decode('utf-8') + '\n')
                f.write('\\small\n')

            if synonyma_entries:
                f.write('\\subsubsection*{Synonyma}\n')
                f.write("\\scriptsize\n")
                f.write('\\begin{itemize}\n')
                for entry in synonyma_entries:
                    entry_text = entry.strip().encode('latex').decode('utf-8')
                    if entry_text:  # only create an \item if the entry contains text
                        f.write('\\item ' + entry_text + '\n')
                f.write('\\end{itemize}\n')
                f.write('\\small\n')

            for subsection in subsections:
                if subsection.text != 'Nálezy' and subsection.text != 'Literatura' and subsection.text != 'Systematika' and subsection.text != 'Synonyma':
                    f.write('\\subsubsection*{' + subsection.text + '}\n')
                    next_node = subsection.find_next_sibling()
                    while next_node and next_node.name != 'h3':
                        if next_node.name == 'p':
                            # Replace <br /> tags with \\ in paragraphs
                            for br in next_node.find_all('br'):
                                br.replace_with('\\\\')
                            if 'Autorství textů:' in next_node.text:
                                f.write('\\subsubsection*{Autorství}\n')
                            f.write(next_node.text + '\n')
                        elif next_node.name == 'table':
                            for link in next_node.find_all('a'):
                                f.write(link.text + '\n')
                        elif next_node.name == 'ul':
                            f.write('\\begin{itemize}\n')
                            for item in next_node.find_all('li'):
                                f.write('\\item ' + item.text + '\n')
                            f.write('\\end{itemize}\n')
                        next_node = next_node.find_next_sibling()
            if literature_entries:
                f.write('\\subsubsection*{Literatura}\n')
                f.write("\\scriptsize\n") 
                f.write('\\begin{itemize}\n')
                for entry in literature_entries:
                    entry_text = entry.text.strip().encode('latex').decode('utf-8')
                    if entry_text:  # only create an \item if the entry contains text
                        f.write('\\item ' + entry_text + '\n')
                f.write('\\end{itemize}\n')
            f.write('\\normalsize\n')  # Restore the font size to the default

    print("Jednotlivé .tex soubory atlasu hub jsou vytvořeny.")
else:
    print("Přeskočeno stahování HTML z myko.cz, předpokládám už existující TeX soubory pro jednotlivé houby.")

# Vytvoření master .tex souboru co všechny dílčí .tex stránky spojí a doplní titulní stranu, font a další parametry
print("")
print("Vytvářím master .tex soubor co spojí jednotlivé .tex soubory dohromady.")
with open('master.tex', 'w') as f:
    f.write('\\documentclass[a4paper]{article}\n')
    f.write('\\usepackage{graphicx}\n')
    f.write('\\usepackage[left=2cm, right=1cm, top=1cm, bottom=2cm]{geometry}\n')
    f.write('\\usepackage{fontspec}\n')
    f.write('\\setmainfont{' + usedfont + '}\n')
    f.write('\\usepackage{polyglossia}\n')
    f.write('\\setdefaultlanguage{czech}\n')
    f.write('\\usepackage{setspace}\n')
    f.write('\\setstretch{0.95}\n')
    f.write('\\usepackage{fontsize}\n')
    f.write('\\fontsize{8pt}{9pt}\\selectfont\n')
    f.write("\\usepackage{etoolbox}\n")
    f.write(r"\usepackage{titlesec}" + "\n\n")
    f.write(r"\titleformat{\subsubsection}[runin]{\normalfont\bfseries}{\thesubsubsection}{1em}{}[\hspace{0.5em}]" + "\n")
    f.write(r"\titlespacing*{\subsubsection}{0pt}{0.5em}{0.5em}" + "\n\n") 
    f.write("\\makeatletter\n")
    f.write("\\patchcmd{\\itemize}{\\def\\makelabel}{\\setlength{\\itemsep}{0pt}\\setlength{\\parskip}{0pt}\\setlength{\\parsep}{0pt}\\def\\makelabel}{}{}\n")
    f.write("\\makeatother\n")
    f.write('\\begin{document}\n')
    f.write('\\pagenumbering{gobble}\n')  # Disable page numbering for the first page
    # Titulní strana s nadpisem, datem a disclaimerem
    f.write('\\begin{titlepage}\n')
    f.write('\\begin{center}\n')
    f.write('\\vspace*{5cm}\n')
    f.write('\\Huge\\textbf{' + maintitle.encode('latex').decode('utf-8') + '}\n\n')
    f.write('\\vspace{1cm}\n')
    f.write('\\LARGE\\textit{' + subtitle.encode('latex').decode('utf-8') + '}\n\n')
    f.write('\\vspace{1cm}\n')
    f.write('\\Large\\textit{' + subsubtitle.encode('latex').decode('utf-8') + '}\n\n')
    f.write('\\vspace{1cm}\n')
    f.write('\\large ' + current_datetime.encode('latex').decode('utf-8') + '\n\n')
    f.write('\\vspace{1cm}\n')
    f.write('\\small ' + disclaimer.encode('latex').decode('utf-8') + '\n')
    f.write('\\end{center}\n')
    f.write('\\end{titlepage}\n')
    for line in lines:
        name = re.search(r'\|(.*?)\]\]', line).group(1)
        filename = name.replace(' ', '_')
        f.write('\\clearpage\n')  # Start each input file on a new page
        f.write('\\input{' + 'tex/' + filename + '.tex' + '}\n')
    f.write('\\end{document}\n')

print("Master .tex vytvořen.")

# Sazba kombinovaného .tex do PDF
print("Překládám master .tex soubor pomocí XeLaTeXu do PDF.")
os.system('xelatex master.tex')

# Přejmenování výsledného PDF dle skupiny hub vybraných na začátku
pdf_filename = 'master.pdf'
new_filename = f"{slugify(subtitle)}.pdf"
os.rename(pdf_filename, new_filename)

print("Hotovo!")
