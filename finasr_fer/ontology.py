DEFAULT_ENTITIES = {
    "en":[
        "NVIDIA","AMD","Intel","Apple","Microsoft","Amazon","Alphabet","Google","Meta Platforms","Tesla",
        "Netflix","Walmart","JPMorgan Chase","Goldman Sachs","Morgan Stanley","Bank of America","Citigroup",
        "BlackRock","Visa","Mastercard","Toyota Motor","Sony Group","MUFG","SoftBank Group","HSBC",
        "UBS","Deutsche Bank","Barclays","Wells Fargo","Broadcom","Qualcomm","TSMC"
    ],
    "zh":[
        "招商银行","平安银行","工商银行","建设银行","中国银行","交通银行","贵州茅台","宁德时代","比亚迪",
        "中国平安","中信证券","腾讯控股","腾讯","阿里巴巴","美团","京东集团","京东","百度","英伟达",
        "NVIDIA","苹果","微软","摩根大通","高盛","贝莱德","海通证券","浦发银行","兴业银行"
    ],
    "ja":[
        "三菱UFJフィナンシャル・グループ","三菱UFJ","三井住友フィナンシャルグループ","三井住友FG",
        "みずほフィナンシャルグループ","みずほFG","野村ホールディングス","大和証券グループ本社",
        "トヨタ自動車","ソニーグループ","日立製作所","キーエンス","ファーストリテイリング",
        "ソフトバンクグループ","NTT","KDDI","任天堂","東京エレクトロン","リクルート",
        "NVIDIA","Apple","JPMorgan Chase","Goldman Sachs"
    ]
}

# Canonical metrics. Surface aliases below are independently searchable and map back to these names.
DEFAULT_METRICS = {
    "en":[
        "revenue","net income","operating income","operating profit","gross profit","free cash flow",
        "capital expenditure","operating expenses","loan-loss provision","credit impairment losses",
        "assets under management","fee margin","loan balance","net interest income","net interest margin",
        "gross margin","operating margin","ROE","ROA","EPS","EBITDA","EBITDA margin","CAGR","WACC","IRR",
        "non-performing loan ratio","CET1 ratio","capital ratio","efficiency ratio","credit spread",
        "risk exposure","guidance","earnings guidance","revenue guidance","capital expenditure guidance",
        "ABS","MBS","CDS","DCF","NAV","ETF","REIT","VaR","FOMC","consensus estimate"
    ],
    "zh":[
        "营业收入","净利润","营业利润","毛利润","自由现金流","资本开支","营业费用","信用减值损失","贷款减值准备",
        "管理资产规模","管理费率","贷款余额","净利息收入","净息差","毛利率","营业利润率","ROE","ROA","EPS","EBITDA",
        "EBITDA利润率","CAGR","WACC","IRR","不良贷款率","核心一级资本充足率","资本充足率","成本收入比",
        "信用利差","风险敞口","指引","业绩指引","收入指引","资本开支指引",
        "FOMC","consensus estimate","ABS","MBS","CDS","DCF","NAV","ETF","REIT","VaR"
    ],
    "ja":[
        "売上高","売上収益","純利益","営業利益","粗利益","フリーキャッシュフロー","設備投資","営業費用",
        "与信費用","貸倒引当金","運用資産残高","運用報酬率","貸出金残高","純金利収入","純金利マージン","粗利益率",
        "営業利益率","ROE","ROA","EPS","EBITDA","EBITDAマージン","CAGR","WACC","IRR","不良債権比率",
        "CET1比率","自己資本比率","経費率","クレジットスプレッド","リスクエクスポージャー",
        "ガイダンス","業績予想","売上高予想","設備投資計画",
        "FOMC","consensus estimate","ABS","MBS","CDS","DCF","NAV","ETF","REIT","VaR"
    ]
}

METRIC_ALIASES = {
    "en":{
        "sales":"revenue","total revenue":"revenue","revenues":"revenue",
        "operating earnings":"operating income","operating profit":"operating profit",
        "capex":"capital expenditure","capital spending":"capital expenditure",
        "opex":"operating expenses","operating expense":"operating expenses",
        "provision for credit losses":"loan-loss provision","credit loss provision":"loan-loss provision",
        "loan loss provision":"loan-loss provision","AUM":"assets under management","management fee margin":"fee margin","fee rate":"fee margin",
        "loans":"loan balance","NIM":"net interest margin","return on equity":"ROE",
        "return on assets":"ROA","nonperforming loan ratio":"non-performing loan ratio",
        "NPL ratio":"non-performing loan ratio","common equity tier 1 ratio":"CET1 ratio"
    },
    "zh":{
        "收入":"营业收入","营收":"营业收入","营业总收入":"营业收入",
        "经营利润":"营业利润","经营费用":"营业费用","运营费用":"营业费用",
        "信贷减值损失":"信用减值损失","贷款损失准备":"贷款减值准备",
        "拨备":"贷款减值准备","AUM":"管理资产规模","管理费率":"管理费率","费率":"管理费率","贷款规模":"贷款余额",
        "净利息收益率":"净息差","NIM":"净息差","不良率":"不良贷款率","NPL率":"不良贷款率",
        "CET1比率":"核心一级资本充足率","一级资本充足率":"核心一级资本充足率"
    },
    "ja":{
        "売上":"売上高","売上収益":"売上収益","営業収益":"売上高",
        "営業益":"営業利益","設備投資額":"設備投資","CAPEX":"設備投資",
        "販管費":"営業費用","営業経費":"営業費用","信用コスト":"与信費用",
        "貸倒引当金繰入額":"貸倒引当金","AUM":"運用資産残高","運用報酬率":"運用報酬率","手数料率":"運用報酬率",
        "貸出残高":"貸出金残高","NIM":"純金利マージン",
        "自己資本利益率":"ROE","総資産利益率":"ROA","不良債権比率":"不良債権比率",
        "普通株式等Tier1比率":"CET1比率"
    }
}

DEFAULT_TERMS = {
    "en":["goodwill impairment","credit spread","duration","convexity","discounted cash flow",
          "credit-risk exposure","liquidity coverage ratio","interest-rate swap","credit default swap",
          "repurchase agreement","convertible bond","value at risk","asset securitization"],
    "zh":["商誉减值","信用利差","久期","凸性","贴现现金流","拨备覆盖率","信用风险暴露","流动性覆盖率",
          "利率互换","信用违约互换","回购协议","可转换债券","风险价值","资产证券化"],
    "ja":["のれんの減損","クレジットスプレッド","デュレーション","コンベクシティ","割引キャッシュフロー",
          "信用リスクエクスポージャー","流動性カバレッジ比率","金利スワップ",
          "クレジット・デフォルト・スワップ","レポ取引","転換社債","バリュー・アット・リスク","資産証券化"]
}

DEFAULT_TICKERS = [
    "NVDA","AMD","INTC","AAPL","MSFT","AMZN","GOOGL","META","TSLA","JPM","GS","MS","BAC","C","BLK",
    "V","MA","TM","SONY","MUFG","600036","000001","601398","601939","601988","600519","300750",
    "002594","601318","600030","0700.HK","9988.HK","3690.HK","9618.HK","9888.HK","8306","8316",
    "8411","8604","8601","7203","6758","6501","6861","9983","9984","9432","9433","7974","8035"
]
DEFAULT_ACRONYMS=["EPS","EBITDA","ROE","ROA","WACC","DCF","CAGR","ETF","REIT","CDS","ABS","MBS","CLO","LBO","AUM","NAV","IRR","VaR","NIM","NPL","CET1"]
