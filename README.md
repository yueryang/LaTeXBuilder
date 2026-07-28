# LaTeXBuilder

This repository enables easy generation of multiple formats for a single manuscript using templates collected from various publishers. 

LaTeX was initially designed to make typesetting easier by separating the content from the formatting. 
However, when draft content is ready for submission before confirming a journal or a conference to submit to, 
or a manuscript has to be submitted to another journal or conference after it is rejected without being sent for peer review, 
it usually takes authors plenty of time to make the draft content or the manuscript adapted to the template of the target journal or conference while maintaining the latest content, 
which is quite inconvenient. 
Especially, it can be highly annoying to merge all the updates to a target template when incomplete content updates are made piecemeal across different templates due to multiple revisions. 
Consequently, we have to design this repository to further separate the content and the formatting via LaTeX and Python. 

All TEX code in this repository follows the LaTeX indentation, which is purely my personal preference. 
Readers are free to adjust and optimize it as needed under equivalent conditions. 
To track your LaTeX, please refer to [LaTeXChecker](https://github.com/yueryang/LaTeXChecker). 

Please check your manuscript carefully before submission. We are not responsible for any direct or indirect losses arising from the use of this repository. 

## Usage

Currently, 9 well-acknowledged templates are deployed. Users should only change the packages and authors' information to adapt to the specified templates. 

- ACMConference
- Elsevier
- IEEEConference
- IEEEJournal
- MDPI
- Nature
- Springer
- TSP
- Wiley

Below describes the structure of the ``LaTeX`` folder and the author's formatting for different publishers. 
It also describes how to mark co-first authors, co-corresponding authors, and multiple affiliations. 
The explanations for co-first authors and co-corresponding authors are not unique. Authors can modify them according to the style of the journal or conference. 
Please note whether the journal or conference allows co-first authors, co-corresponding authors, or multiple affiliations, and whether some "special" journals use the universal template from the publisher. 
This repository will be updated as soon as there are new templates or updates for existing templates that become available. 

This repository uses examples such as San Zhang, Si Li, Wu Wang, Liu Zhao, Qi Sun, etc. Email addresses and ORCIDs are also examples based on names. 
Unless the institution does not provide an email address or the institution's email system is very poor (e.g., email loss, notification failures, or lacks even basic auto-reply functionality), 
the institution's email address should be used. Gmail is used here as a temporary substitute. If any actual email address or ORCID is pointed to, please contact us for correction. 

Furthermore, I recently saw some authors online claiming that the cross symbol indicates a deceased author. 
However, to our recollection, some journals and conferences do use the cross symbol to mark co-first authors, and the IEEE journal template directly outputs the cross symbol by ``\IEEEauthorrefmark{2}``. 
After consulting a librarian, it is said that the hash symbol is the most common way to mark co-first authors, followed by the cross. 
To indicate a deceased author, please use a box around their name instead of a cross. 
Our summary of recommended symbols for marking co-first authors is as follows: 
- Elsevier: Follow the template instruction. No need to specify a symbol. 
- IEEE conference: Directly use "1st" or the cross symbol. 
- IEEE journal: Use the cross symbol. 
- Others: Use the hash symbol. 

If you have a bad memory or want to completely avoid misunderstandings, you can consistently use the hash symbol (code: ``\#``) to mark co-first authors, 
except for Elsevier templates and IEEE conference templates that allow "1st". 

### Content

Please write your paper title, abstract, keywords, content, and references here. 

Please note that it is required to **specifically change the title in the Springer and the Wiley templates** while modifying the ``./Content/title.tex`` file. 

### Figure

Please include your figures (with their corresponding sources like ``.pptx`` if you wish to) here. It is highly recommended to use figures in the PDF format and vector graphics recognized by ``\includegraphics``. 

### Elsevier

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

### Springer

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

### IEEE Conference

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

### IEEE Journal

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

### ACM Conference

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

### TSP

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

### MDPI

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

### Nature

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

## Regards

If you are viewing this repository as an author whose manuscript is always rejected without being sent for peer review, it is my genuine hope that your paper can be accepted in the journal or conference you submit to. 

May every academic paper in the world receive the respect it deserves and go to the right place. 

## Citation

If you wish to cite this work, please use the following BibTeX. 

```
@inproceedings{liu2024efficient,
  title={An efficient information retrieval and tracking algorithm for multiple typesetting styles of the same paper},
  author={Liu, Yingying and Li, Yuan and Tang, Jiyue and Ji, Tong and Xu, Xiaoyu and Luo, Yuxin and Lin, Yifeng and Yang, Yuer and Wu, Yubing},
  booktitle={2024 7th International Conference on Data Science and Information Technology (DSIT)},
  pages={1--6},
  year={2024},
  organization={IEEE}
}
```

Thank you for your citations. 

## Forgetting and Forgiveness

The paper mentioned above is the official academic paper that corresponds to this repository. It has already passed peer review, been published by the IEEE publisher, and been indexed by the EI database. 

People who format their papers based on this repository may forget to rewrite their Data Availability statements, which results in guiding reviewers to this repository. 

In these situations, we would appreciate it if reviewers could ask the authors for correct Data Availability statements instead of rejecting papers directly. 

---

# LaTeXBuilder

本存储库搜集了来自不同出版社的模板，可以轻松为同一份手稿生成多种排版格式。

LaTeX 最初的设计理念是将内容与格式分离，从而简化排版。
然而，当内容已经就绪但未确定要投的期刊或会议，或者手稿未送审就被拒稿不得不转投至其它期刊或会议时，作者通常需要花费大量时间在保持内容最新的情况下将内容或手稿适配到目标期刊或会议的模板，这十分不方便。
尤其是多次修稿导致在不同模板中零散地进行内容更新时，将所有更新合并到目标模板会令人恼火。
因此，我们设计了这个存储库，旨在通过 LaTeX 和 Python 进一步分离内容和格式。

本存储库中的所有 TEX 代码遵循 LaTeX 缩进，纯属本人的偏好，使用时读者可以随意在等效的情况下进行调整和优化。
要追踪您的 LaTeX，请参阅 [LaTeXChecker](https://github.com/yueryang/LaTeXChecker)。

请在投稿前仔细检查您的手稿，我们对因使用本存储库而产生的任何直接或间接损失不承担任何责任。

## 用法

目前已部署的 9 个较为著名的模板如下，理论上，若要手动操作，用户只需修改宏包和作者信息即可适配指定的模板。

- ACMConference
- Elsevier
- IEEEConference
- IEEEJournal
- MDPI
- Nature
- Springer
- TSP
- Wiley

下文将介绍文件夹 ``LaTeX`` 的结构以及不同出版社的作者排版，介绍时会顺便告知如何标记共一、共同通讯和多个单位。
解释共同第一作者和共同通讯作者的文字部分不唯一，作者可以根据期刊或会议的风格进行修改。
请注意期刊或会议是否允许共一、共同通讯或多个单位，并注意某些“搞特殊”的期刊是否统一使用出版社的通用模板。
如果有新的模板或已有模板有更新可用，本存储库会尽快更新。

本存储库以张三李四王五赵六孙七等举例，邮箱和 ORCID 也是依照名字编的例子。
除非单位未提供邮箱或单位的邮箱收发系统很差（例如经常丢失邮件、不会通知或连最基本的自动回复功能都没有），否则邮箱一般使用单位邮箱，这里先使用 gmail 替代着。
如果指向了真实存在的邮箱和 ORCID，恳请联系我们笔者。

此外，我们在网络上看到部分作者认为十字架符号表示已故的作者，但在我们笔者中确实存在一些期刊或会议使用十字架符号来标记共同第一作者，而且 IEEE 期刊模板中直接 ``\IEEEauthorrefmark{2}`` 出来的就是十字架符号。
后来问了下图书馆的老师，用井号标记共一的最多，十字架符号次之。若要表示作者已故，使用框框框住名字，而不是标十字架。
个人总结了下，标记共同第一作者的符号建议是：Elsevier 模板，遵循模板指引，不需要自己指定符号；IEEE 会议模板，直接 1st 或者用十字架符号；IEEE 期刊模板，用十字架符号；其它模板，用井号。
如果记性不好或希望完全避免误会，可统一使用井号（代码为 ``\#``）来标记共一（Elsevier 模板和允许 1st 的 IEEE 会议模板除外）。

### 内容

请在此文件夹的相应文件中填写论文标题、摘要、关键词、正文和参考文献。

请注意，在修改 ``./Content/title.tex`` 文件时，**Springer 和 Wiley 模板中的标题必须进行修改**。

### 图表

请在此文件夹中放置您的图表（如果需要，请附上相应的文件来源，例如“.pptx”）。强烈建议使用 PDF 或能够被 ``\includegraphics`` 命令识别的矢量图形的格式的图表。

### Elsevier 出版社下的期刊

最好看的模板，不接受反驳。在 ``\title`` 和 ``\begin{abstract}`` 之间插入作者信息，``\author`` 后的中括号接的是作者单位，支持多单位排版。使用 ``\fnmark[1]`` 标记共同第一作者，使用 ``\cormark[1]`` 标记通讯作者；使用 ``\nonumnote`` 解释通讯记号，使用 ``\fntext[1]`` 解释共一记号。在 Elsevier 模板中，单位会用字母显示，共一会用数字显示。
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

### Springer 出版社下的期刊

在 ``\title`` 和 ``\maketitle`` 之间放置以下内容，``\inst`` 中标记单位，支持多单位排版。在 ``\inst`` 内，使用 ``\#`` 标记共一，使用 ``*`` 标记通讯。

```
\author{
	San Zhang\inst{1,2,3,\#}
	\and Si Li\inst{1,2,\#}
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

在 ``\maketitle`` 和 ``\begin{abstract}`` 之间放置以下内容解释共一和共同通讯记号，其中 ``\renewcommand{\thefootnote}{}`` 用于移除 ``\footnotetext`` 自带的标记符。这些命令需要放置在 ``\maketitle`` 后是因为这些命令需要向一个有效的页面添加脚注，如果放在 ``\maketitle`` 前，会有一个含有部分脚注的空白页在正文之前。此处感谢博文 [https://blog.csdn.net/qq_34331113/article/details/121642975](https://blog.csdn.net/qq_34331113/article/details/121642975) 的博主。下文中 ``\url`` 最开始源自 ``\usepackage{url}``，目前建议使用 ``\usepackage{xurl}`` 实现自动换行的 ``\url``（如有需要还可以进一步添加换行处理代码）。读者也可使用 ``\href`` 或者添加 ``mailto:`` 前缀。

```
\renewcommand{\thefootnote}{}
\footnotetext{\textsuperscript{\#} Co-first authors contributed equally to this work. }
\footnotetext{* Corresponding author(s): Liu Zhao (\url{liuzhao@gmail.com}) and Qi Sun (\url{qisun@gmail.com}). }
```

### IEEE 会议

在 ``\title`` 和 ``\maketitle`` 之间使用以下内容，其中 ``\linebreakand`` 抄自 [https://blog.csdn.net/lgl123ok/article/details/121033610](https://blog.csdn.net/lgl123ok/article/details/121033610)，需要作者自行根据姓名单位的长短决定在哪里进行换行，有兴趣者可以编写自动排版程式。貌似不支持多单位排版，如果需要可以使用分号硬塞（吧）。另外，如果会议要求移除作者前的序号标记，可以参考 IEEE 期刊排版辅以 ``\thanks`` 命令标记共一。

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

另外，如果会议主办方要求移除引用记号外的框框，可以在导言区加入以下代码。

```
\hypersetup{
	colorlinks=false,
	linkbordercolor=white,
	pdfborderstyle={/S/U/W 1}, % remove box
	hidelinks
}
```

调整标题字号为四号加粗可将 ``\title`` 命令作如下修改：

```
\title{\fontsize{12pt}{14.4pt}\selectfont \textbf{Your Title}}
```

若要两栏末尾对齐，则可导入以下宏包：

```
\usepackage{flushend}
```

### IEEE 期刊

风格类似于 IEEE 会议，但略有不同。如果使用 IEEE 会议的模板排版 IEEE 期刊，大概率会出问题。另外，IEEE 每个期刊都有自己的一个模板，可从 [https://template-selector.ieee.org/secure/templateSelector/publicationType](https://template-selector.ieee.org/secure/templateSelector/publicationType) 进行选择和下载。此处的作者排版说明将按最大的通用性进行。同理，在 ``\title`` 和 ``\maketitle`` 之间使用以下内容，使用 ``\textsuperscript{\#}`` 标记共一，``*`` 标记通讯作者，``\thanks`` 变成了单位说明（完整句子那种）。

```
\author{
	San Zhang\textsuperscript{\#}\thanks{San Zhang was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A; the Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B; and the Department/College/School/Faculty/Institute/... C, University C, City C, Country/Region C. }, 
	Si Li\textsuperscript{\#}\thanks{Si Li was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A and the Department/College/School/Faculty/Institute/... B, University B, City B, Country/Region B. }, 
	Wu Wang\thanks{Wu Wang was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}, 
	Liu Zhao*\thanks{Liu Zhao was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}, 
	and Qi Sun*\thanks{Qi Sun was with the Department/College/School/Faculty/Institute/... A, University A, City A, Country/Region A}
	\thanks{\textsuperscript{\#}San Zhang and Si Li are the co-first authors who contributed equally to this work. }
	\thanks{*Liu Zhao (\protect\url{liuzhao@gmail.com}) and Qi Sun (\protect\url{qisun@gmail.com}) are the corresponding authors. }
}
```

### ACM 会议

类似地，在 ``\title`` 和 ``\maketitle`` 之间使用以下内容。

```
\author{San Zhang\textsuperscript{\#}}
\affiliation{%
	\institution{Department/College/School/Faculty/\\Institute/... A, University A}
	\streetaddress{Street A}
	\city{City A}
	\country{Country/Region A}
}
\email{sanzhang@gmail.com}
\orcid{0000-0000-0000-0003}

\author{Si Li\textsuperscript{\#}}
\affiliation{%
	\institution{Department/College/School/Faculty/\\Institute/... B, University B}
	\streetaddress{Street B}
	\city{City B}
	\country{Country/Region B}
}
\email{sili@gmail.com}
\orcid{0000-0000-0000-0004}

\author{Wu Wang}
\affiliation{%
	\institution{Department/College/School/Faculty/\\Institute/... C, University C}
	\streetaddress{Street C}
	\city{City C}
	\country{Country/Region C}
}
\email{wuwang@gmail.com}
\orcid{0000-0000-0000-0005}

\author{Liu Zhao*}
\affiliation{%
	\institution{Department/College/School/Faculty/\\Institute/... D, University D}
	\streetaddress{Street D}
	\city{City D}
	\country{Country/Region D}
}
\email{liuzhao@gmail.com}
\orcid{0000-0000-0000-0006}

\author{Qi Sun*}
\affiliation{%
	\institution{Department/College/School/Faculty/\\Institute/... E, University E}
	\streetaddress{Street E}
	\city{City E}
	\country{Country/Region E}
}
\email{qisun@gmail.com}
\orcid{0000-0000-0000-0007}

\renewcommand{\shortauthors}{Zhang S, Li S, Wang W, et al. }
```

类似地，在 ``\maketitle`` 和 ``\begin{abstract}`` 之间放置以下内容解释共一和共同通讯记号。

```
\renewcommand{\thefootnote}{}
\footnotetext{\textsuperscript{\#} Co-first authors contributed equally to this work. }
\footnotetext{* Corresponding author(s): Liu Zhao (\url{liuzhao@gmail.com}) and Qi Sun (\url{qisun@gmail.com}). }
```

### Wiley 出版社旗下的刊物

Wiley 的作者单位标记类似于 Elsevier，因此一个作者对应多个单位或一个单位对应多个作者的情况十分容易处理。但相比于 Elsevier，Wiley 似乎没有提供标记共同第一作者的代码。标记共一、共同通讯和共同通讯说明可以考虑使用以下代码，该代码需要放置在 ``\begin{document}`` 后、``\maketitle`` 之前，且建议放置在 ``\title`` 和 ``\titlemark`` 之后。

```
\author[1,2,3]{San Zhang}
\author[1,2]{Si Li}
\author[1]{Wu Wang}
\author[1]{Liu Zhao}
\author[1]{Qi Sun}
\authormark{Zhang S, Li S, Wang W, \textsc{et al.} }

\address[1]{\orgdiv{Department/College/School/Faculty/Institute/... A}, \orgname{University A}, \orgaddress{\state{Street A}, \country{Country A}}}
\address[2]{\orgdiv{Department/College/School/Faculty/Institute/... B}, \orgname{University B}, \orgaddress{\state{Street B}, \country{Country B}}}
\address[3]{\orgdiv{Department/College/School/Faculty/Institute/... C}, \orgname{University C}, \orgaddress{\state{Street C}, \country{Country C}}}

\corres{Corresponding authors: Liu Zhao and Qi Sun \email{liuzhao@gmail.com (Liu Zhao), qisun@gmail.com (Qi Sun)}}
```

使用以下代码实现共一说明（没有符号），放置在 ``\maketitle`` 之后。

```
\renewcommand\thefootnote{}
\footnotetext{San Zhang and Si Li are the co-first authors contributing equally to this work. }
```

### TSP 出版社旗下的刊物

模板风格类似于 Elsevier，出版社模板主动提供共一和通讯的标注方式。在 ``\Title`` 和 ``\abstract`` 之间使用以下内容即可实现共一和共同通讯。

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

### MDPI 出版社旗下的刊物

模板风格类似于 TSP，出版社模板主动提供共一和通讯的标注方式。在 ``\Title`` 和 ``\abstract`` 之间使用以下内容即可实现共一和共同通讯。

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

## 祝福

如果您是一位稿件总是未经同行评审就被拒收的作者，那么我真诚地希望您提交的论文能够被您投稿的期刊或会议接受。

愿世间的每一篇论文都能得到应有的尊重，都能去到适合的地方。

## 引用

如果您希望引用我们的工作，请使用以下 BibTeX。

```
@inproceedings{liu2024efficient,
  title={An efficient information retrieval and tracking algorithm for multiple typesetting styles of the same paper},
  author={Liu, Yingying and Li, Yuan and Tang, Jiyue and Ji, Tong and Xu, Xiaoyu and Luo, Yuxin and Lin, Yifeng and Yang, Yuer and Wu, Yubing},
  booktitle={2024 7th International Conference on Data Science and Information Technology (DSIT)},
  pages={1--6},
  year={2024},
  organization={IEEE}
}
```

感谢您的引用。

## 遗忘与原谅

上述论文是与此存储库对应的正式学术论文。它已通过同行评审，由 IEEE 出版社出版，并被 EI 数据库收录。

基于此存储库格式化论文的人员可能会忘记重写其数据可用性声明，从而导致审稿人误以为此存储库提供数据。

在这种情况下，我们希望审稿人能够要求作者提供正确的数据可用性声明，而不是直接拒稿。
