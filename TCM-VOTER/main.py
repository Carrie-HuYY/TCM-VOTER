import analysis, report, output, get, compute
import os
import time
from datetime import datetime
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('network_pharmacology_analysis.log')
    ]
)
logger = logging.getLogger(__name__)


def from_chemical(chemical_id,
                  score=990,
                  DiseaseName="cough",
                  target_max_number=70,
                  report_number=0,
                  interaction_number=0,
                  out_for_excel=True,
                  out_for_cytoscape=True,
                  research_status_test=True,
                  safety_research=True,
                  out_graph=True,
                  re=True,
                  path='results'):
    """
    Perform classical forward network pharmacology analysis with logging

    Args:
        chemical_id: Chemical ID to analyze
        score (int): Combined score threshold. Default is 990.
        out_for_excel (bool): Output Excel files. Default is True.
        out_for_cytoscape (bool): Output for Cytoscape. Default is True.
        research_status_test (bool): Perform research status test. Default is True.
        safety_research (bool): Perform safety research. Default is True.
        out_graph (bool): Output visualization. Default is True.
        re (bool): Return raw results. Default is True.
        path (str): Output directory. Default is 'results'.

    Returns:
        Various DataFrames containing analysis results or 0 if re=False
        :param path:
        :param re:
        :param out_graph:
        :param safety_research:
        :param research_status_test:
        :param out_for_cytoscape:
        :param out_for_excel:
        :param interaction_number:
        :param report_number:
        :param chemical_id:
        :param score:
        :param target_max_number:
        :param DiseaseName:
    """
    # 记录开始时间
    start_time = time.time()
    logger.info("Starting network pharmacology analysis...")

    try:
        # 数据获取阶段
        logger.info("Fetching chemical data...")
        chem = get.get_chemicals('DNCID', chemical_id)

        logger.info("Fetching protein links data...")
        chem_protein_links = get.get_chem_protein_links('DNCID', chemical_id, score=score)

        logger.info("Fetching protein data...")
        proteins = get.get_proteins('Ensembl_ID', chem_protein_links['Ensembl_ID'])

        logger.info("Fetching TCM-chemical links...")
        tcm_chem_links = get.get_tcm_chem_links('DNCID', chem['DNCID'])

        logger.info("Fetching TCM data...")
        tcm = get.get_tcm('DNHID', tcm_chem_links['DNHID'])

        logger.info("Fetching formula-TCM links...")
        formula_tcm_links = get.get_formula_tcm_links('DNHID', tcm['DNHID'])

        logger.info("Fetching formula data...")
        formula = get.get_formula('DNFID', formula_tcm_links['DNFID'])

        logger.info("Fetching SD-formula links...")
        sd_formula_links = get.get_SD_Formula_links('DNFID', formula['DNFID'])

        logger.info("Fetching SD data...")
        sd = get.get_SD('DNSID', sd_formula_links['DNSID'])

        # 转换为DataFrame
        logger.info("Converting data to DataFrames...")
        SD_df = pd.DataFrame(sd)
        SD_Formula_Links_df = pd.DataFrame(sd_formula_links)
        formula_df = pd.DataFrame(formula)
        formula_tcm_links_df = pd.DataFrame(formula_tcm_links)
        tcm_df = pd.DataFrame(tcm)
        tcm_chem_links_df = pd.DataFrame(tcm_chem_links)
        chem_df = pd.DataFrame(chem)
        chem_protein_links_df = pd.DataFrame(chem_protein_links)
        protein_df = pd.DataFrame(proteins)

        # 可视化输出
        if out_graph:
            logger.info("Generating network visualizations...")
            output.vis(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                       tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

        # Cytoscape输出
        if out_for_cytoscape:
            logger.info("Preparing files for Cytoscape...")
            output.out_for_cyto(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                                tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

        # Excel输出
        if out_for_excel:
            logger.info("Writing results to Excel file...")
            with pd.ExcelWriter(f"{path}/results.xlsx") as writer:
                SD_df.to_excel(writer, sheet_name="辩证信息", index=False)
                SD_Formula_Links_df.to_excel(writer, sheet_name="辩证-复方信息", index=False)
                formula_df.to_excel(writer, sheet_name="复方信息", index=False)
                formula_tcm_links_df.to_excel(writer, sheet_name="复方-中药连接", index=False)
                tcm_df.to_excel(writer, sheet_name="中药信息", index=False)
                tcm_chem_links_df.to_excel(writer, sheet_name="中药-化合物连接", index=False)
                chem_df.to_excel(writer, sheet_name="化合物信息", index=False)
                chem_protein_links_df.to_excel(writer, sheet_name="化合物-靶点连接", index=False)
                protein_df.to_excel(writer, sheet_name="靶点信息", index=False)

        # 研究状态测试
        if research_status_test:
            logger.info("Performing research status test...")

            analysis.update_config(DiseaseName, target_max_number, report_number, interaction_number)

            protein_research_test = protein_df['gene_name']
            protein_research_test = pd.DataFrame(protein_research_test)

            df_expanded = protein_research_test.copy()
            df_expanded["split_values"] = df_expanded["gene_name"].str.split(r"[\s/]+")
            df_expanded = df_expanded.explode("split_values")

            df_expanded = pd.DataFrame(df_expanded['split_values'])
            df_expanded.rename(columns={"split_values": "gene_name"}, inplace=True)
            df_expanded.to_excel("Protein_List.xlsx", index=False)

            analysis.research_status_test(f"Protein_List.xlsx")

        # 安全性研究
        if safety_research:
            logger.info("Performing safety research analysis...")
            protein_df = pd.DataFrame(protein_df['gene_name'])
            chem_df = pd.DataFrame(chem_df['Name'])
            formula_df = pd.DataFrame(formula_df['name'])
            tcm_df = pd.DataFrame(tcm_df['cn_name'])

            toxic_formula, toxic_herb, toxic_chemical, toxic_protein = report.filter_toxic_data(
                protein_df, chem_df, formula_df, tcm_df
            )

            report.generate_toxicity_report(toxic_formula, toxic_herb, toxic_chemical, toxic_protein)

        # 计算并记录总时间
        elapsed_time = time.time() - start_time
        logger.info(f"Analysis completed successfully in {elapsed_time:.2f} seconds")

        if re:
            return SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df, tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df
        else:
            return 0

    except Exception as e:
        logger.error(f"Error occurred during analysis: {str(e)}", exc_info=True)
        raise

def from_tcm_or_formula(tcm_or_formula_id,
                        proteins_id=None,
                        score=990,
                        DiseaseName="cough",
                        target_max_number=70,
                        report_number=0,
                        interaction_number=0,
                        out_for_excel=True,
                        out_for_cytoscape=True,
                        research_status_test=True,
                        safety_research=True,
                        out_graph=True,
                        re=True,
                        path='results'):
    """
    Perform classical forward network pharmacology analysis

    Args:
        tcm_or_formula_id: Any iterable that supports 'in' operation, containing TCM or formula IDs to analyze.
        proteins_id: None or any iterable that supports 'in' operation, containing Ensembl_IDs of proteins to analyze.
                    Default is None.
        score (int): Only records with combined_score >= score in HerbiV_chemical_protein_links will be selected.
                    Default is 990.
        out_for_cytoscape (bool): Whether to output files for Cytoscape visualization. Default is True.
        out_graph (bool): Whether to output ECharts-based HTML network visualization. Default is True.
        re (bool): Whether to return raw analysis results (TCM, compounds, proteins and their connections).
        path (str): Directory to store results.
        research_status_test:
        out_for_excel:

    Returns:
        formula: Formula information (only returned when input is HVPID).
        formula_tcm_links: Formula-TCM connection info (only returned when input is HVPID).
        tcm: TCM information.
        tcm_chem_links: TCM-compound connections.
        chem: Compound information.
        chem_protein_links: Compound-protein connections.
        proteins: Protein information.
        :param path:
        :param re:
        :param out_graph:
        :param safety_research:
        :param research_status_test:
        :param out_for_excel:
        :param out_for_cytoscape:
        :param interaction_number:
        :param report_number:
        :param target_max_number:
        :param score:
        :param proteins_id:
        :param tcm_or_formula_id:
        :param DiseaseName:
    """


    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

    logger.info("Starting network pharmacology analysis")

    # Step 1: Get formula/TCM information
    logger.info("Fetching formula/TCM information")
    if tcm_or_formula_id[0][2] == 'F':  # Check if input is formula
        formula = get.get_formula('DNFID', tcm_or_formula_id)
        formula_tcm_links = get.get_formula_tcm_links('DNFID', formula['DNFID'])
        tcm = get.get_tcm('DNHID', formula_tcm_links['DNHID'])
        sd_formula_links = get.get_SD_Formula_links('DNFID', formula['DNFID'])
        sd = get.get_SD('DNSID', sd_formula_links['DNSID'])
    else:
        tcm = get.get_tcm('DNHID', tcm_or_formula_id)
        formula_tcm_links = get.get_formula_tcm_links('DNHID', tcm['DNHID'])
        formula = get.get_formula('DNFID', formula_tcm_links['DNFID'])
        sd_formula_links = get.get_SD_Formula_links('DNFID', formula['DNFID'])
        sd = get.get_SD('DNSID', sd_formula_links['DNSID'])

    # Step 2: Get chemical information
    logger.info("Fetching TCM-chemical links")
    tcm_chem_links = get.get_tcm_chem_links('DNHID', tcm['DNHID'])
    logger.info("Fetching chemical information")
    chem = get.get_chemicals('DNCID', tcm_chem_links['DNCID'])

    # Step 3: Get protein information
    logger.info(f"Fetching chem-protein links with score >= {score}")
    chem_protein_links = get.get_chem_protein_links('DNCID', chem['DNCID'], score)

    if proteins_id is None:
        logger.info("Fetching protein information")
        proteins = get.get_proteins('Ensembl_ID', chem_protein_links['Ensembl_ID'])
    else:
        logger.info("Fetching specified protein information")
        proteins = get.get_proteins('Ensembl_ID', proteins_id)

    # Convert to DataFrames
    logger.info("Converting results to DataFrames")
    SD_df = pd.DataFrame(sd)
    SD_Formula_Links_df = pd.DataFrame(sd_formula_links)
    formula_df = pd.DataFrame(formula)
    formula_tcm_links_df = pd.DataFrame(formula_tcm_links)
    tcm_df = pd.DataFrame(tcm)
    tcm_chem_links_df = pd.DataFrame(tcm_chem_links)
    chem_df = pd.DataFrame(chem)
    chem_protein_links_df = pd.DataFrame(chem_protein_links)
    protein_df = pd.DataFrame(proteins)

    # Output visualization
    if out_graph:
        logger.info("Generating visualization")
        output.vis(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                   tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

    # Output for Cytoscape
    if out_for_cytoscape:
        logger.info("Generating Cytoscape output")
        output.out_for_cyto(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                            tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

    # Output to Excel
    if out_for_excel:
        logger.info("Writing results to Excel")
        with pd.ExcelWriter(f"{path}/results.xlsx") as writer:
            SD_df.to_excel(writer, sheet_name="辩证信息", index=False)
            SD_Formula_Links_df.to_excel(writer, sheet_name="辩证-复方信息", index=False)
            formula_df.to_excel(writer, sheet_name="复方信息", index=False)
            formula_tcm_links_df.to_excel(writer, sheet_name="复方-中药连接", index=False)
            tcm_df.to_excel(writer, sheet_name="中药信息", index=False)
            tcm_chem_links_df.to_excel(writer, sheet_name="中药-化合物连接", index=False)
            chem_df.to_excel(writer, sheet_name="化合物信息", index=False)
            chem_protein_links_df.to_excel(writer, sheet_name="化合物-靶点连接", index=False)
            protein_df.to_excel(writer, sheet_name="靶点信息", index=False)

    # Research status test
    if research_status_test:
        logger.info("Performing research status test")

        analysis.update_config(DiseaseName, target_max_number, report_number, interaction_number)

        protein_research_test = protein_df['gene_name']
        protein_research_test = pd.DataFrame(protein_research_test)

        df_expanded = protein_research_test.copy()
        df_expanded["split_values"] = df_expanded["gene_name"].str.split(r"[\s/]+")
        df_expanded = df_expanded.explode("split_values")

        df_expanded = pd.DataFrame(df_expanded['split_values'])
        df_expanded.rename(columns={"split_values": "gene_name"}, inplace=True)
        df_expanded.to_excel("Protein_List.xlsx", index=False)

        analysis.research_status_test(f"Protein_List.xlsx")

    # Safety research (placeholder)
    if safety_research:
        logger.info("Performing safety research test")

        protein_df = pd.DataFrame(protein_df['gene_name'])
        chem_df = pd.DataFrame(chem_df['Name'])
        formula_df = pd.DataFrame(formula_df['name'])
        tcm_df = pd.DataFrame(tcm_df['cn_name'])

        toxic_formula, toxic_herb, toxic_chemical, toxic_protein = report.filter_toxic_data(
            protein_df, chem_df, formula_df, tcm_df
        )

        report.generate_toxicity_report(toxic_formula, toxic_herb, toxic_chemical, toxic_protein)

    logger.info("Analysis completed")

    if re:
        return SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df, tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df
    else:
        return 0


def from_proteins(proteins,
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
                  random_state=None,
                  num=1000,
                  tcm_component=False,
                  formula_component=False,
                  re=True,
                  path='results/'):

    # 初始化计时和日志
    start_time = time.time()
    def log_step(step_name):
        elapsed = time.time() - start_time
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Step: {step_name}] | Time elapsed: {elapsed:.2f}s")

    # 创建输出目录
    log_step("Creating output directory")
    if not os.path.exists(path):
        os.makedirs(path)

    # 逐步执行并记录时间
    log_step("Fetching proteins")
    proteins = get.get_proteins('Ensembl_ID', proteins)

    log_step("Fetching chem-protein links")
    chem_protein_links = get.get_chem_protein_links('Ensembl_ID', proteins['Ensembl_ID'], score)
    if chem_protein_links.empty:
        raise ValueError(f"未找到化合物-蛋白质连接(score={score})，请降低score值")

    log_step("Fetching chemicals")
    chem = get.get_chemicals('DNCID', chem_protein_links['DNCID'])

    log_step("Fetching TCM-chem links")
    tcm_chem_links = get.get_tcm_chem_links('DNCID', chem['DNCID'])

    log_step("Fetching TCMs")
    tcm = get.get_tcm('DNHID', tcm_chem_links['DNHID'])

    log_step("Fetching formula-TCM links")
    formula_tcm_links = get.get_formula_tcm_links('DNHID', tcm['DNHID'])

    log_step("Fetching formulas")
    formula = get.get_formula('DNFID', formula_tcm_links['DNFID'])

    log_step("Fetching SD-formula links")
    sd_formula_links = get.get_SD_Formula_links('DNFID', formula['DNFID'])

    log_step("Fetching SDs")
    sd = get.get_SD('DNSID', sd_formula_links['DNSID'])

    log_step("Computing scores")
    tcm, chem, formula = compute.score(tcm, tcm_chem_links, chem,
                                      chem_protein_links, formula, formula_tcm_links)

    tcms, formulas = None, None
    if tcm_component:
        log_step("Computing TCM components")
        tcms = compute.component(tcm.loc[tcm['Importance Score'] != 1.0], random_state, num)
    if formula_component:
        log_step("Computing formula components")
        formulas = compute.component(formula.loc[formula['Importance Score'] != 1.0], random_state, num)

    # 转换为 DataFrame
    log_step("Converting to DataFrames")
    SD_df = pd.DataFrame(sd)
    SD_Formula_Links_df = pd.DataFrame(sd_formula_links)
    formula_df = pd.DataFrame(formula)
    formula_tcm_links_df = pd.DataFrame(formula_tcm_links)
    tcm_df = pd.DataFrame(tcm)
    tcm_chem_links_df = pd.DataFrame(tcm_chem_links)
    chem_df = pd.DataFrame(chem)
    chem_protein_links_df = pd.DataFrame(chem_protein_links)
    protein_df = pd.DataFrame(proteins)

    # 输出结果
    if out_for_cytoscape:
        log_step("Exporting for Cytoscape")
        output.out_for_cyto(SD_df, SD_Formula_Links_df, formula_df,
                           formula_tcm_links_df, tcm_df,
                           tcm_chem_links_df, chem_df,
                           chem_protein_links_df, protein_df, path)

    if out_graph:
        log_step("Generating graphs")
        output.vis(SD_df, SD_Formula_Links_df, formula_df,
                  formula_tcm_links_df, tcm_df,
                  tcm_chem_links_df, chem_df,
                  chem_protein_links_df, protein_df, path)

    if out_for_excel:
        log_step("Exporting to Excel")
        with pd.ExcelWriter(f"{path}/results.xlsx") as writer:
            SD_df.to_excel(writer, sheet_name="辩证信息", index=False)
            SD_Formula_Links_df.to_excel(writer, sheet_name="辩证-复方信息", index=False)
            formula_df.to_excel(writer, sheet_name="复方信息", index=False)
            formula_tcm_links_df.to_excel(writer, sheet_name="复方-中药连接", index=False)
            tcm_df.to_excel(writer, sheet_name="中药信息", index=False)
            tcm_chem_links_df.to_excel(writer, sheet_name="中药-化合物连接", index=False)
            chem_df.to_excel(writer, sheet_name="化合物信息", index=False)
            chem_protein_links_df.to_excel(writer, sheet_name="化合物-靶点连接", index=False)
            protein_df.to_excel(writer, sheet_name="靶点信息", index=False)

    if research_status_test:
        log_step("Running research status test")
        analysis.update_config(DiseaseName, target_max_number, report_number, interaction_number)

        protein_research_test = protein_df['gene_name'].to_frame()
        df_expanded = protein_research_test.assign(
            split_values=protein_research_test['gene_name'].str.split(r"[\s/]+")
        ).explode("split_values")[['split_values']].rename(columns={"split_values": "gene_name"})
        df_expanded.to_excel("Protein_List.xlsx", index=False)
        analysis.research_status_test("Protein_List.xlsx")

    if safety_research:
        log_step("Safety research (placeholder)")

        protein_df = pd.DataFrame(protein_df['gene_name'])
        chem_df = pd.DataFrame(chem_df['Name'])
        formula_df = pd.DataFrame(formula_df['name'])
        tcm_df = pd.DataFrame(tcm_df['cn_name'])

        toxic_formula, toxic_herb, toxic_chemical, toxic_protein = report.filter_toxic_data(
            protein_df, chem_df, formula_df, tcm_df
        )

        report.generate_toxicity_report(toxic_formula, toxic_herb, toxic_chemical, toxic_protein)

    log_step("Completed")
    if re:
        return (SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df,
                tcms, formulas)


def from_SD(SD_ID,
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
            ):
    """
    从中医辨证开始，构建中药整合药理学

    Args: (原有参数说明保持不变)
    """
    # 初始化计时和日志
    start_time = time.time()

    def log_step(step_name):
        elapsed = time.time() - start_time
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [Step: {step_name}] | Time elapsed: {elapsed:.2f}s")

    log_step("Creating output directory")
    if not os.path.exists(path):
        os.makedirs(path)

    log_step("Fetching SD data")
    SD = get.get_SD('DNSID', SD_ID)

    log_step("Fetching SD-Formula links")
    SD_Formula_Links = get.get_SD_Formula_links('DNSID', SD['DNSID'])

    log_step("Fetching formulas")
    formula = get.get_formula('DNFID', SD_Formula_Links['DNFID'])

    log_step("Fetching formula-TCM links")
    formula_tcm_links = get.get_formula_tcm_links('DNFID', formula['DNFID'])

    log_step("Fetching TCMs")
    tcm = get.get_tcm('DNHID', formula_tcm_links['DNHID'])

    log_step("Fetching TCM-chem links")
    tcm_chem_links = get.get_tcm_chem_links('DNHID', tcm['DNHID'])

    log_step("Fetching chemicals")
    chem = get.get_chemicals('DNCID', tcm_chem_links['DNCID'])

    log_step("Fetching chem-protein links")
    chem_protein_links = get.get_chem_protein_links('DNCID', chem['DNCID'], score=score)

    log_step("Fetching proteins")
    protein = get.get_proteins('Ensembl_ID', chem_protein_links['Ensembl_ID'])

    log_step("Converting to DataFrames")
    # 转换为DataFrame
    SD_df = pd.DataFrame(SD)
    SD_Formula_Links_df = pd.DataFrame(SD_Formula_Links)
    formula_df = pd.DataFrame(formula)
    formula_tcm_links_df = pd.DataFrame(formula_tcm_links)
    tcm_df = pd.DataFrame(tcm)
    tcm_chem_links_df = pd.DataFrame(tcm_chem_links)
    chem_df = pd.DataFrame(chem)
    chem_protein_links_df = pd.DataFrame(chem_protein_links)
    protein_df = pd.DataFrame(protein)

    if out_graph:
        log_step("Generating visualization graphs")
        output.vis(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                   tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

    if out_for_cytoscape:
        log_step("Exporting for Cytoscape")
        output.out_for_cyto(SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                            tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df, path)

    if out_for_excel:
        log_step("Exporting to Excel")
        with pd.ExcelWriter(f"{path}/results.xlsx") as writer:
            SD_df.to_excel(writer, sheet_name="辩证信息", index=False)
            SD_Formula_Links_df.to_excel(writer, sheet_name="辩证-复方信息", index=False)
            formula_df.to_excel(writer, sheet_name="复方信息", index=False)
            formula_tcm_links_df.to_excel(writer, sheet_name="复方-中药连接", index=False)
            tcm_df.to_excel(writer, sheet_name="中药信息", index=False)
            tcm_chem_links_df.to_excel(writer, sheet_name="中药-化合物连接", index=False)
            chem_df.to_excel(writer, sheet_name="化合物信息", index=False)
            chem_protein_links_df.to_excel(writer, sheet_name="化合物-靶点连接", index=False)
            protein_df.to_excel(writer, sheet_name="靶点信息", index=False)

    if research_status_test:
        log_step("Running research status test")
        analysis.update_config(DiseaseName, target_max_number, report_number, interaction_number)

        protein_research_test = protein_df['gene_name']
        protein_research_test = pd.DataFrame(protein_research_test)

        df_expanded = protein_research_test.copy()
        df_expanded["split_values"] = df_expanded["gene_name"].str.split(r"[\s/]+")
        df_expanded = df_expanded.explode("split_values")

        df_expanded = pd.DataFrame(df_expanded['split_values'])
        df_expanded.rename(columns={"split_values": "gene_name"}, inplace=True)
        df_expanded.to_excel("Protein_List.xlsx", index=False)

        analysis.research_status_test(f"Protein_List.xlsx")

    if safety_research:
        log_step("Running safety research")

        protein_df = pd.DataFrame(protein_df['gene_name'])
        chem_df = pd.DataFrame(chem_df['Name'])
        formula_df = pd.DataFrame(formula_df['name'])
        tcm_df = pd.DataFrame(tcm_df['cn_name'])

        toxic_formula, toxic_herb, toxic_chemical, toxic_protein = report.filter_toxic_data(
            protein_df, chem_df, formula_df, tcm_df
        )

        report.generate_toxicity_report(toxic_formula, toxic_herb, toxic_chemical, toxic_protein)

    log_step("Completed all operations")
    if re:
        return (SD_df, SD_Formula_Links_df, formula_df, formula_tcm_links_df,
                tcm_df, tcm_chem_links_df, chem_df, chem_protein_links_df, protein_df)
    else:
        return 0


def TCM_VOTER(SearchType,
              SearchName,
              DiseaseName="cough",
              target_max_number=70,
              report_number=0,
              interaction_number=0,
              score=990,
              out_graph=True,
              out_for_cytoscape=True,
              out_for_excel=True,
              research_status_test=True,
              safety_research=True,
              re=True,
              path='results/'
              ):

    if SearchType == 0:
        SearchID = get.get_SD('证候', SearchName)['DNSID']

        from_SD(SearchID,
                score=score,
                DiseaseName=DiseaseName,
                target_max_number=target_max_number,
                report_number=report_number,
                interaction_number=interaction_number,
                out_graph=out_graph,
                out_for_cytoscape=out_for_cytoscape,
                out_for_excel=out_for_excel,
                research_status_test=research_status_test,
                safety_research=safety_research,
                re=re,
                path=path
                )

    if SearchType == 1:

        SearchID = get.get_formula('name', SearchName)['DNFID']

        from_tcm_or_formula(SearchID, score=score,
                            DiseaseName=DiseaseName,
                            target_max_number=target_max_number,
                            report_number=report_number,
                            interaction_number=interaction_number,
                            out_graph=out_graph,
                            out_for_cytoscape=out_for_cytoscape,
                            out_for_excel=out_for_excel,
                            research_status_test=research_status_test,
                            safety_research=safety_research,
                            re=re,
                            path=path
                            )

    if SearchType == 2:

        SearchID = get.get_tcm('cn_name', SearchName)['DNHID']

        from_tcm_or_formula(SearchID, score=score,
                            DiseaseName=DiseaseName,
                            target_max_number=target_max_number,
                            report_number=report_number,
                            interaction_number=interaction_number,
                out_graph=out_graph,
                out_for_cytoscape=out_for_cytoscape,
                out_for_excel=out_for_excel,
                research_status_test=research_status_test,
                safety_research=safety_research,
                re=re,
                path=path
                )

    if SearchType == 3:

        SearchID = get.get_chemicals('Name', SearchName)['DNCID']

        from_chemical(SearchID, score=score,
                      DiseaseName=DiseaseName,
                      target_max_number=target_max_number,
                      report_number=report_number,
                      interaction_number=interaction_number,
                out_graph=out_graph,
                out_for_cytoscape=out_for_cytoscape,
                out_for_excel=out_for_excel,
                research_status_test=research_status_test,
                safety_research=safety_research,
                re=re,
                path=path
                )

    if SearchType == 4:

        SearchID = get.get_proteins('gene_name', SearchName)['Ensembl_ID']

        from_proteins(SearchID, score=score,
                      DiseaseName=DiseaseName,
                      target_max_number=target_max_number,
                      report_number=report_number,
                      interaction_number=interaction_number,
                        out_graph=out_graph,
                        out_for_cytoscape=out_for_cytoscape,
                        out_for_excel=out_for_excel,
                        research_status_test=research_status_test,
                        safety_research=safety_research,
                        re=re,
                        path=path
                        )


    return 0



if __name__ == '__main__':
    TCM_VOTER(SearchType=2,
              SearchName=['人参'],
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

    #from_tcm_or_formula(['DNH0158'])
    #from_chemical(['DNC0007'], score=0)
    #from_SD(['DNS0001'])
    #from_proteins(['ENSP00000000233'], score=660, out_for_cytoscape=True, out_graph=True, tcm_component=False, formula_component=False)