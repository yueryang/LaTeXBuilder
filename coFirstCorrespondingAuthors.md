# coFirstCorrespondingAuthors

This project aims to provide corner-case typesetting for co-first and co-corresponding authors in LaTeX. 

See [https://blog.csdn.net/weixin_45726033/article/details/143378135](https://blog.csdn.net/weixin_45726033/article/details/143378135) in Chinese if necessary. 

---

## Elsevier

This must be the most beautiful template, with no objections accepted. 

Insert author information between ``\title`` and ``\begin{abstract}``. The square brackets after ``\author`` are followed by the author's unit, which supports multi-unit typesetting. Use ``\fnmark[1]`` to mark the co-first author, and ``\cormark[1]`` to mark the corresponding author; use ``\nonumnote`` to explain the corresponding note, and use ``\fntext[1]`` to explain the co-author note. In the Elsevier template, the unit will be displayed as a letter, and the co-author will be displayed as a number. 

```
\author[1,2,3]{San Zhang}[orcid=0000-0000-0000-0003]\fnmark[1]
\ead{sanzhang@gmail.com}

\author[1,2]{Si Li}[orcid=0000-0000-0000-0004]\fnmark[1]
\ead{sili@gmail.com}

\author[1]{Wu Wang}[orcid=0000-0000-0000-0005]
\ead{wuwang@gmail.com}

\author[1]{Liu Zhao}[orcid=0000-0000-0000-0006]\cormark[1]
\ead{liuzhao@gmail.com}

\author[1]{Qi Sun}[orcid=0000-0000-0000-0007]\cormark[1]
\ead{qisun@gmail.com}

\address[1]{Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}
\address[2]{Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B}
\address[3]{Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C}

\nonumnote{* These are the corresponding authors. } % \nonumnote{* This is the corresponding author. } 
\fntext[1]{Co-first authors contributed equally to this work. } 
```

---

## Springer

Place the following between ``\title`` and ``\maketitle``. Use ``\inst`` to mark the units and support multi-unit typesetting. In ``\inst``, use ``\dag`` to mark common units and ``*`` to mark correspondence. 

```
\author{
	San Zhang\inst{1,2,3,\dag}
	\and Si Li\inst{1,2,\dag}
	\and Wu Wang\inst{1}
	\and Liu Zhao\inst{1,*}
	\and Qi Sun\inst{1,*}
}

\authorrunning{Zhang S et al. }

\institute{
	Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A
	\and Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B
	\and Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C
}
```

Place the following content between ``\maketitle`` and ``\begin{abstract}`` to explain common and common communication marks, where ``\renewcommand{\thefootnote}{}`` is used to remove the markup of ``\footnotetext``. These commands need to be placed after ``\maketitle`` because they need to add footnotes to a valid page. If placed before ``\maketitle``, there will be a blank page with partial footnotes before the main text. In the following text, ``\url`` is derived from ``\usepackage{url}``. You can also use ``\href`` or add the ``mailto:`` prefix. 

```
\renewcommand{\thefootnote}{}
\footnotetext{\textsuperscript{\dag} Co-first authors contributed equally to this work. }
\footnotetext{* Corresponding author(s): Liu Zhao (\url{liuzhao@gmail.com}) and Qi Sun (\url{qisun@gmail.com}). }
```

---

## IEEE Conference

Define the ``\linebreakand`` command in the introduction area. 

```
\makeatletter
\newcommand{\linebreakand}{%
  \end{@IEEEauthorhalign}
  \hfill\mbox{}\par
  \mbox{}\hfill\begin{@IEEEauthorhalign}
}
\makeatother
```

Use the following between ``\title`` and ``\maketitle``. The author needs to decide where to break the line according to the length of the name unit. Those who are interested can write an automatic typesetting program. It seems that multi-unit typesetting is not supported. If necessary, you can use semicolons to force it (right). In addition, if the conference requires the removal of the serial number mark before the author, you can refer to the IEEE journal typesetting and use the ``\thanks`` command to mark it as one. 

```
\author{
	\IEEEauthorblockN{1\textsuperscript{st} San Zhang}
	\IEEEauthorblockA{
		\textit{Department/College/School/Faculty/Institute/... A} \\
		\textit{University A} \\
		City A, Country/Region A \\
		\url{sanzhang@gmail.com}
	}
	\and
	\IEEEauthorblockN{1\textsuperscript{st} Si Li}
	\IEEEauthorblockA{
		\textit{Department/College/School/Faculty/Institute/... B} \\
		\textit{University B} \\
		City B, Country/Region B \\
		\url{sili@gmail.com}
	}
	\and
	\IEEEauthorblockN{2\textsuperscript{nd} Wu Wang}
	\IEEEauthorblockA{
		\textit{Department/College/School/Faculty/Institute/... C} \\
		\textit{University C} \\
		City C, Country/Region C \\
		\url{wuwang@e.ntu.edu.sg}
	}
	\linebreakand
	\IEEEauthorblockN{3\textsuperscript{rd} Liu Zhao*}
	\IEEEauthorblockA{
		\textit{Department/College/School/Faculty/Institute/... D} \\
		\textit{University D} \\
		City D, Country/Region D \\
		\url{liuzhao@gmail.com}
	}
	\and
	\IEEEauthorblockN{4\textsuperscript{th} Qi Sun*\thanks{* These are the corresponding authors. }}
	\IEEEauthorblockA{
		\textit{Department/College/School/Faculty/Institute/... E} \\
		\textit{University E} \\
		City E, Country/Region E \\
		\url{qisun@gmail.com}
	}
}
```

Alternatively, if the conference organizer requests that the quote box be removed, the following code may be added to the introduction area. 

```
\hypersetup{
	colorlinks=false,
	linkbordercolor=white,
	pdfborderstyle={/S/U/W 1}, % remove box
	hidelinks
}
```

To adjust the title font size to 4 bold, you can modify the ``\title`` command as follows: 

```
\title{\fontsize{12pt}{14.4pt}\selectfont \textbf{Your Title}}
```

If you want to align the ends of the two columns, you can import the following macro package: 

```
\usepackage{flushend}
```

---

## IEEE Journal

The style is similar to that of IEEE conferences, but slightly different. If you use the template of the IEEE conference to typeset an IEEE journal, there is a high probability that there will be problems. In addition, each IEEE journal has its own template, which can be selected and downloaded from [https://template-selector.ieee.org/secure/templateSelector/publicationType](https://template-selector.ieee.org/secure/templateSelector/publicationType). The author typesetting instructions here will be as general as possible. Similarly, use the following content between ``\title`` and ``\maketitle``, use ``\textsuperscript{\textdagger}`` to mark common, ``*`` to mark the corresponding author, and ``\thanks`` becomes a unit description (the kind of complete sentence). 

```
\author{
	San Zhang\textsuperscript{\textdagger}\thanks{San Zhang was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A; the Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B; and the Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C. }, 
	Si Li\textsuperscript{\textdagger}\thanks{Si Li was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A and the Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B. }, 
	Wu Wang\thanks{Wu Wang was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}, 
	Liu Zhao*\thanks{Liu Zhao was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}, 
	and Qi Sun*\thanks{Qi Sun was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}
	\thanks{\textsuperscript{\textdagger}San Zhang and Si Li are the co-first authors who contributed equally to this work. }
	\thanks{*Liu Zhao (\url{liuzhao@gmail.com}) and Qi Sun (\url{qisun@gmail.com}) are the corresponding authors. }
}
```

## ACM Conference

Similarly, use the following between ``\title`` and ``\maketitle``. 

```
\author{San Zhang\textsuperscript{#}}
\affiliation{%
	\institution{Department/College/School/Faculty/Institute/... A, University A}
	\streetaddress{Street A}
	\city{City A}
	\country{Country/Region A}
}
\email{sanzhang@gmail.com}
\orcid{0000-0000-0000-0003}

\author{Si Li\textsuperscript{#}}
\affiliation{%
	\institution{Department/College/School/Faculty/Institute/... B, University B}
	\streetaddress{Street B}
	\city{City B}
	\country{Country/Region B}
}
\email{sili@gmail.com}
\orcid{0000-0000-0000-0004}

\author{Wu Wang}
\affiliation{%
	\institution{Department/College/School/Faculty/Institute/... C, University C}
	\streetaddress{Street C}
	\city{City C}
	\country{Country/Region C}
}
\email{wuwang@gmail.com}
\orcid{0000-0000-0000-0005}

\author{Liu Zhao*}
\affiliation{%
	\institution{Department/College/School/Faculty/Institute/... D, University D}
	\streetaddress{Street D}
	\city{City D}
	\country{Country/Region D}
}
\email{liuzhao@gmail.com}
\orcid{0000-0000-0000-0006}

\author{Qi Sun*}
\affiliation{%
	\institution{Department/College/School/Faculty/Institute/... E, University E}
	\streetaddress{Street E}
	\city{City E}
	\country{Country/Region E}
}
\email{qisun@gmail.com}
\orcid{0000-0000-0000-0007}

\renewcommand{\shortauthors}{Zhang S, Li S, Wang W, et al. }
```

Similarly, place the following between ``\maketitle`` and ``\begin{abstract}`` to explain the common identity and common correspondence notation. 

```
\renewcommand{\thefootnote}{}
\footnotetext{\textsuperscript{\dag} Co-first authors contributed equally to this work. }
\footnotetext{* Corresponding author(s): Liu Zhao (\url{liuzhao@gmail.com}) and Qi Sun (\url{qisun@gmail.com}). }
```

## TSP

The style of TSP is similar to that of Elsevier. The template actively offers marking ways of co-first and co-corresponding authors. Use the following between ``\Title`` and ``\abstract`` to achieve co-first and co-coresponding authors. 
```
\newcommand{\orcidauthorA}{0000-0000-0000-0003}
\newcommand{\orcidauthorB}{0000-0000-0000-0004}
\newcommand{\orcidauthorC}{0000-0000-0000-0005}
\newcommand{\orcidauthorD}{0000-0000-0000-0006}
\newcommand{\orcidauthorE}{0000-0000-0000-0007}

\Author{
	San Zhang\textsuperscript{1,2,3,\#}\orcidA{}, 
	Si Li\textsuperscript{1,2,\#}\orcidB{}, 
	Wu Wang\textsuperscript{1}\orcidC{}, 
	Liu Zhao\textsuperscript{1,*}\orcidD{}, 
	and Qi Sun\textsuperscript{1,*}\orcidE{}
}

\AuthorNames{San Zhang, Si Li, Wu Wang, et al. }

\address{%
	\textsuperscript{1} Department/College/School/Faculty/Institute/... A, University A, City A, Code A, Country A
		
	\textsuperscript{2} Department/College/School/Faculty/Institute/... B, University B, City B, Code B, Country B
	
	\textsuperscript{3} Department/College/School/Faculty/Institute/... C, University C, City C, Code C, Country C
}

\corres{Corresponding Author(s): Liu Zhao and Qi Sun. Email: liuzhao@gmail.com and qisun@gmail.com}

\firstnote{These authors contributed equally to this work} 
\secondnote{}
```

## MDPI

The style of MDPI is close to that of TSP. The template actively offers marking ways of co-first and co-corresponding authors. Use the following between ``\Title`` and ``\abstract`` to achieve co-first and co-coresponding authors. 

```
\newcommand{\orcidauthorA}{0000-0000-0000-0003} % Add \orcidA{} behind the author's name
\newcommand{\orcidauthorB}{0000-0000-0000-0004} % Add \orcidB{} behind the author's name
\newcommand{\orcidauthorC}{0000-0000-0000-0005} % Add \orcidC{} behind the author's name
\newcommand{\orcidauthorD}{0000-0000-0000-0006} % Add \orcidD{} behind the author's name
\newcommand{\orcidauthorE}{0000-0000-0000-0007} % Add \orcidE{} behind the author's name

\Author{San Zhang$^{1,2,3}$\orcidA{}, Si Li$^{1,2}$\orcidB{}, Wu Wang$^1$\orcidC{}, Liu Zhao$^1$\orcidD{}*, and Qi Sun$^1$\orcidE{}*}

\AuthorNames{San Zhang, Si Li, Wu Wang, Liu Zhao, Qi Sun}

\address{%
	$^{1}$ \quad Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A;\\
	$^{2}$ \quad Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B;\\
	$^{3}$ \quad Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C;
}

\corres{Correspondence: liuzhao@gmail.com; qisun@gmail.com; }

\firstnote{Current address: Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A. }
```

## Nature

The style of Nature is close to that of Elsevier. The template actively offers marking ways of co-first and co-corresponding authors. Use the following between ``\title`` and ``\keywords`` to achieve co-first and co-coresponding authors. 

```
\author[1,2,3,+]{San Zhang}
\author[1,2,+]{Si Li}
\author[1]{Wu Wang}
\author[1,*]{Liu Zhao}
\author[1,*]{Qi Sun}
\affil[1]{Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}
\affil[2]{Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B}
\affil[3]{Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C}
\affil[+]{These authors contributed equally to this work. }
\affil[*]{Corresponding authors: Liu Zhao (liuzhao@gmail.com) and Qi Sun (qisun@gmail.com)}
```

---

Wish you all the best! 
