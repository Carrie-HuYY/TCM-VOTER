# TCM-VOTER (中药网络药理学数据库)

***TCM-VOTER*** (Traditional Chinese Medicine - Visualization - Omics and Text driven Target Enrichment and Research): 
一个聚焦于网络结构，基于组学与文本挖掘的靶标富集与药理学研究工具

从网络药理学和中医理论视角出发，构建"辩证-方剂-中药-成分-靶点"网络，同时开发多种分析功能的网络药理学数据库。
- 1.基于文本挖掘对候选蛋白或基因进行筛选和分类，缩小实验验证范围。 
- 2.纳入中药毒理学的安全性评估筛选算法，辅助构建中药毒理学网络。
- 3.基于大量病历数据的中医辩证预测，中医角度辅助老药新用和靶点寻找。
- 4.开发组方优化算法/成分评价算法/可视化方案

- [1. 简介](#简介)

- [2. 安装](#安装)

- [3. 使用](#使用)
  - [3.1 from_SD：从辩证出发](#from_sd)
  - [3.2 from_TCM_or_Formula：从中药/方剂出发](#from_tcm_or_formula)
  - [3.3 from_proteins：从靶点出发](#from_protein)

- [4. 结果展示](#结果展示)
  - [4.1 基于pyecharts的可交互图](#out_graph)
  - [4.2 可用于cytoscape绘图的文件](#out_for_cytoscape)
  - [4.3 保存结果的excel表格](#out_for_excel)
  - [4.4 靶点研究进展的查询结果](#research_status_test)
  - [4.5 安全性评估结果](#safety_research)

- [5. 注意](#注意)
  - [5.1 关于Python版本问题](#1关于python版本)
  - [5.2 关于数据下载问题](#2关于数据下载)

## 简介



## 安装

可以使用pip安装TCM-VOTER

```cmd
pip install TCM-VOTER
```

requirement包括(Python版本需要≥3.9，其余没有强制要求)

```cmd
pandas~=1.3.5
rdkit~=2023.3.2
tqdm~=4.67.1
pyecharts~=2.0.7
numpy~=1.21.6
```

## 使用

### `TCM-VOTER函数`


```python
from TCM-VOTER import main

main.TCM_VOTER(SearchType,
               SearchName,
               score=990,
               DiseaseName="cough",
               target_max_number=70,
               report_number=0,
               interaction_number=0,
               out_graph=True,
               out_for_cytoscape=True,
               out_for_excel=True,
               research_status_test=True, 
               safety_research=True,
               re=True,
               path='results/'
                    )
```

`from_SD`需要两个个必需形参`SearchType`：可以用来判断检索的类型（详见下表）；`SearchName`：可以用于检索的内容，如果是`0`那就输入某种方剂名，
具体数据可见[数据集](/TCM-VOTER/Data/)

| SearchType | Source |
|------------|--------|
| 0          | 辩证     |
| 1          | 方剂     |
| 2          | 中药     |
| 3          | 成分     |
| 4          | 靶点     |



`from_SD`的可选形参有：
- `score`: int类型，[Chemical_Protein_Links数据集](/TCM-VOTER/Data/Chemical_Protein_Links.xlsx)中仅combined_score大于等于score的记录会被筛选出，默认为990； 
- `DiseaseName`:str类型，可用于在pubmed文献中检索靶点同该疾病的对应关系，即是否同时出现过用于研究价值评定，默认为`cough` 
- `target_max_number`:int类型，筛选出来的靶点数量最大值，默认为`70` 
- `report_number`:int类型，要求至少出现报道过的次数，默认为`0`；
- `interaction_number`:int类型，存在相互作用的蛋白数量，即最少应该和几个差异表达蛋白列表中的蛋白相互作用,默认为`0`；
- `out_graph`: boolean类型，是否输出基于ECharts的html格式的网络可视化图，默认为`False`；
- `out_for_cytoscape`: boolean类型，是否输出用于Cytoscape绘图的文件，默认为`False`；
- `our_for_excel`: boolean类型，是否将结果输出到excel中，默认为`True`；
- `research_status_test`: boolean类型，是否将得到的靶点进行研究价值评定，默认为`False`；
- `safety_research`: boolean类型，是否对得到的靶点进行安全性研究，默认为`False`；
- `re`: boolean类型，是否返回原始分析结果（辩证、复方、中药、化合物（中药成分）、蛋白（靶点）及其连接信息），
默认为True。若re为True，则函数将返回运行结果sd、sd_formula_links.xlsx, formula、formula_tcm_links、tcm、tcm_chem_links、chem、
chem_protein_links和proteins，它们均为pd.DataFrame类型，分别存储了辩证信息、辩证-复方连接信息，
复方信息、复方-中药连接信息、中药信息、中药-化合物（中药成分）连接信息、化合物（中药成分）信息、 化合物（中药成分）-蛋白（靶点）连接信息和蛋白（靶点）信息；
- `path`: str类型，存放结果的路径，默认为`results/`。若无此路径，将自动建立相应的目录。


## 结果展示

### 可视化绘图(out_graph)

`out_graph`提供了两种可交互的可视化方案，[范例1](/README_pictures/out_graph_0.png)和[范例2](/README_pictures/out_graph_1.png)

### 输出可用于Cytoscape作图的文件(out_for_cytoscape)

`out_for_cytoscape`给出了可以直接用于cytoscape绘图的两个文件，`type.csv`和`network.csv`，其中格式分别如下：

***type.csv***

| Key        | Attribute  |
|------------|------------|
| glucose    | Chemicals  |
| glucose    | Chemicals  |

***network.csv***

| SourceNode   | TargetNode          |
|--------------|---------------------|
| testosterone |  NR3C4              |
| testosterone | SHBG                |
| testosterone | IGFBP3              |

### 输出excel(out_for_excel)

输出一个名为`results.xlsx`的文件，按照不同的文件名分为函数得到的数据，

### 研究价值评估(research_status_test)

根据中药网络药理学筛选得到的差异表达蛋白（DEPs）或基因（DEGs），进而从
中筛选出已有FDA批准或临床试验药物的靶点，排除无对应药物的候选蛋白，最后给出药物推荐表格，
以及两种可视化方案：[图1](README_pictures/Reasearch_0.png)，[图2](README_pictures/Reasearch_1.png)

### 安全性评估(safety_research)



## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=Carrie-HuYY/DualNet-TCM&type=Date)](https://star-history.com/#Carrie-HuYY/DualNet-TCM&Date)

## 注意

### 1.关于Python版本

由于在 Python 3.9 之前的版本中，`tuple[...]` 和 `list[...]` 
这样的类型注解语法不被支持。
Python 3.9 引入了原生的类型注解支持（PEP 585），
但在早期版本中，需要使用 typing 模块中的 Tuple、List 等类型. 所以需要Python≥3.9，如果＜3.9的话，
可将`compute.py`函数中修改如下：

```python
from typing import Tuple, Union

def score(weights: Union[dict, None] = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # 函数逻辑
    pass
```

### 2.关于数据下载
整体大小为9个G，由于百度网盘限制，所以拆分成三个压缩包，解压后放data/文件夹即可

[下载链接1](https://pan.baidu.com/s/1zIlTjstJMscKdZnP30wc1g?pwd=2n2t) 

[下载链接2](https://pan.baidu.com/s/1tg8WQtJiJi70A8HIRYG_PA?pwd=9bvh) 

[下载链接3](https://pan.baidu.com/s/1tg8WQtJiJi70A8HIRYG_PA?pwd=9bvh)
