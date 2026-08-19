"""
知识库加载器
提供常识性知识检查功能
"""

import os
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class KnowledgeRecord:
    """知识记录"""
    id: str
    category: str  # 历史、地理、科学
    topic: str
    content: str
    keywords: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class KnowledgeLoader:
    """知识库加载器"""
    
    def __init__(self, data_dir: Optional[str] = None):
        """
        初始化知识库加载器
        
        Args:
            data_dir: 知识数据目录路径
        """
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.data_dir = data_dir
        self.records: List[KnowledgeRecord] = []
        self._loaded = False
    
    def load(self) -> List[KnowledgeRecord]:
        """
        加载知识库
        
        Returns:
            知识记录列表
        """
        if self._loaded:
            return self.records
        
        self.records = []
        
        # 加载历史知识
        self._load_history()
        
        # 加载地理知识
        self._load_geography()
        
        # 加载科学知识
        self._load_science()
        
        self._loaded = True
        print(f"[知识库] 加载完成: {len(self.records)} 条记录")
        return self.records
    
    def _load_history(self):
        """加载历史知识"""
        history_data = [
            # 中国历史朝代
            {"id": "hist_001", "topic": "夏朝", "content": "夏朝（约前2070-前1600年）是中国史书中记载的第一个世袭制朝代，由大禹的儿子启建立。", "keywords": ["夏朝", "大禹", "启", "世袭制"]},
            {"id": "hist_002", "topic": "商朝", "content": "商朝（约前1600-前1046年）是中国第一个有直接文字记载的朝代，甲骨文是商朝的文字。", "keywords": ["商朝", "甲骨文", "商汤", "纣王"]},
            {"id": "hist_003", "topic": "周朝", "content": "周朝（约前1046-前256年）分为西周和东周，东周又分为春秋和战国时期。", "keywords": ["周朝", "西周", "东周", "春秋", "战国"]},
            {"id": "hist_004", "topic": "秦朝", "content": "秦朝（前221-前207年）由秦始皇嬴政建立，是中国历史上第一个统一的中央集权国家。", "keywords": ["秦朝", "秦始皇", "嬴政", "统一"]},
            {"id": "hist_005", "topic": "汉朝", "content": "汉朝（前202-220年）分为西汉和东汉，汉武帝时期国力达到鼎盛。", "keywords": ["汉朝", "西汉", "东汉", "汉武帝"]},
            {"id": "hist_006", "topic": "三国", "content": "三国时期（220-280年）包括魏、蜀、吴三个政权，由曹丕、刘备、孙权分别建立。", "keywords": ["三国", "魏", "蜀", "吴", "曹操", "刘备", "孙权"]},
            {"id": "hist_007", "topic": "唐朝", "content": "唐朝（618-907年）是中国历史上最强盛的朝代之一，唐太宗李世民开创贞观之治。", "keywords": ["唐朝", "唐太宗", "李世民", "贞观之治"]},
            {"id": "hist_008", "topic": "宋朝", "content": "宋朝（960-1279年）分为北宋和南宋，经济文化高度发达，但军事较弱。", "keywords": ["宋朝", "北宋", "南宋", "赵匡胤"]},
            {"id": "hist_009", "topic": "元朝", "content": "元朝（1271-1368年）由蒙古族建立，忽必烈是第一位皇帝。", "keywords": ["元朝", "忽必烈", "蒙古"]},
            {"id": "hist_010", "topic": "明朝", "content": "明朝（1368-1644年）由朱元璋建立，永乐年间郑和下西洋。", "keywords": ["明朝", "朱元璋", "郑和", "永乐"]},
            {"id": "hist_011", "topic": "清朝", "content": "清朝（1636-1912年）由满族建立，是中国最后一个封建王朝。", "keywords": ["清朝", "满族", "康熙", "乾隆"]},
            
            # 世界历史
            {"id": "hist_012", "topic": "古埃及", "content": "古埃及文明发源于尼罗河流域，金字塔是古埃及法老的陵墓。", "keywords": ["古埃及", "金字塔", "法老", "尼罗河"]},
            {"id": "hist_013", "topic": "古希腊", "content": "古希腊文明是西方文明的源头，雅典民主制是最早的民主制度之一。", "keywords": ["古希腊", "雅典", "民主", "苏格拉底"]},
            {"id": "hist_014", "topic": "古罗马", "content": "古罗马从共和国发展为帝国，罗马法对西方法律影响深远。", "keywords": ["古罗马", "罗马帝国", "罗马法"]},
            {"id": "hist_015", "topic": "文艺复兴", "content": "文艺复兴（14-17世纪）起源于意大利，是欧洲思想文化解放运动。", "keywords": ["文艺复兴", "意大利", "达芬奇", "米开朗基罗"]},
            {"id": "hist_016", "topic": "工业革命", "content": "工业革命（18-19世纪）始于英国，蒸汽机的发明标志着工业时代的开始。", "keywords": ["工业革命", "蒸汽机", "英国"]},
            {"id": "hist_017", "topic": "法国大革命", "content": "法国大革命（1789-1799年）推翻了波旁王朝，传播了自由平等思想。", "keywords": ["法国大革命", "巴士底狱", "自由平等"]},
            {"id": "hist_018", "topic": "美国独立", "content": "美国独立战争（1775-1783年）使美国脱离英国殖民统治，1776年发表《独立宣言》。", "keywords": ["美国独立", "独立宣言", "华盛顿"]},
            {"id": "hist_019", "topic": "第一次世界大战", "content": "第一次世界大战（1914-1918年）是帝国主义列强之间的战争，同盟国战败。", "keywords": ["一战", "同盟国", "协约国"]},
            {"id": "hist_020", "topic": "第二次世界大战", "content": "第二次世界大战（1939-1945年）是法西斯轴心国与反法西斯同盟国之间的战争。", "keywords": ["二战", "法西斯", "希特勒"]},
        ]
        
        for item in history_data:
            record = KnowledgeRecord(
                id=item["id"],
                category="历史",
                topic=item["topic"],
                content=item["content"],
                keywords=item["keywords"],
                metadata={"category": "历史"}
            )
            self.records.append(record)
    
    def _load_geography(self):
        """加载地理知识"""
        geography_data = [
            # 中国地理
            {"id": "geo_001", "topic": "长江", "content": "长江是中国最长的河流，全长6300公里，流经11个省市。", "keywords": ["长江", "河流", "中国"]},
            {"id": "geo_002", "topic": "黄河", "content": "黄河是中国第二长河，全长5464公里，是中华文明的发源地。", "keywords": ["黄河", "河流", "中华文明"]},
            {"id": "geo_003", "topic": "长城", "content": "长城是中国古代的军事防御工程，总长度超过2万公里。", "keywords": ["长城", "防御", "秦始皇"]},
            {"id": "geo_004", "topic": "珠穆朗玛峰", "content": "珠穆朗玛峰是世界最高峰，海拔8848.86米，位于中国与尼泊尔边境。", "keywords": ["珠穆朗玛峰", "最高峰", "喜马拉雅"]},
            {"id": "geo_005", "topic": "青藏高原", "content": "青藏高原是世界上海拔最高的高原，被称为'世界屋脊'。", "keywords": ["青藏高原", "世界屋脊", "高原"]},
            {"id": "geo_006", "topic": "塔克拉玛干沙漠", "content": "塔克拉玛干沙漠是中国最大的沙漠，位于新疆塔里木盆地。", "keywords": ["塔克拉玛干", "沙漠", "新疆"]},
            {"id": "geo_007", "topic": "京杭大运河", "content": "京杭大运河是世界上最长的人工运河，全长1794公里。", "keywords": ["京杭大运河", "运河", "人工"]},
            {"id": "geo_008", "topic": "台湾海峡", "content": "台湾海峡是台湾岛与中国大陆之间的海峡，最窄处约130公里。", "keywords": ["台湾海峡", "台湾", "海峡"]},
            
            # 世界地理
            {"id": "geo_009", "topic": "亚马逊河", "content": "亚马逊河是世界上流量最大的河流，位于南美洲。", "keywords": ["亚马逊河", "河流", "南美洲"]},
            {"id": "geo_010", "topic": "撒哈拉沙漠", "content": "撒哈拉沙漠是世界上最大的热带沙漠，位于非洲北部。", "keywords": ["撒哈拉", "沙漠", "非洲"]},
            {"id": "geo_011", "topic": "地中海", "content": "地中海是世界上最大的陆间海，连接大西洋和印度洋。", "keywords": ["地中海", "陆间海", "欧洲"]},
            {"id": "geo_012", "topic": "太平洋", "content": "太平洋是世界上最大、最深的大洋，面积约占地球表面积的三分之一。", "keywords": ["太平洋", "大洋", "地球"]},
            {"id": "geo_013", "topic": "大西洋", "content": "大西洋是世界第二大洋，位于欧洲、非洲与南北美洲之间。", "keywords": ["大西洋", "大洋"]},
            {"id": "geo_014", "topic": "喜马拉雅山脉", "content": "喜马拉雅山脉是世界上最高的山脉，位于亚洲，横跨5个国家。", "keywords": ["喜马拉雅", "山脉", "亚洲"]},
            {"id": "geo_015", "topic": "落基山脉", "content": "落基山脉是北美洲最大的山脉，纵贯北美大陆。", "keywords": ["落基山脉", "山脉", "北美洲"]},
            {"id": "geo_016", "topic": "尼罗河", "content": "尼罗河是世界上最长的河流，全长6650公里，位于非洲。", "keywords": ["尼罗河", "河流", "非洲"]},
            {"id": "geo_017", "topic": "贝加尔湖", "content": "贝加尔湖是世界上最深的湖泊，位于俄罗斯。", "keywords": ["贝加尔湖", "湖泊", "俄罗斯"]},
            {"id": "geo_018", "topic": "里海", "content": "里海是世界上最大的湖泊，位于欧洲和亚洲交界处。", "keywords": ["里海", "湖泊"]},
            {"id": "geo_019", "topic": "马六甲海峡", "content": "马六甲海峡是世界上最重要的航运通道之一，连接太平洋和印度洋。", "keywords": ["马六甲海峡", "海峡", "航运"]},
            {"id": "geo_020", "topic": "苏伊士运河", "content": "苏伊士运河连接地中海和红海，是亚洲与非洲的分界线。", "keywords": ["苏伊士运河", "运河", "埃及"]},
        ]
        
        for item in geography_data:
            record = KnowledgeRecord(
                id=item["id"],
                category="地理",
                topic=item["topic"],
                content=item["content"],
                keywords=item["keywords"],
                metadata={"category": "地理"}
            )
            self.records.append(record)
    
    def _load_science(self):
        """加载科学知识"""
        science_data = [
            # 物理学
            {"id": "sci_001", "topic": "牛顿第一定律", "content": "牛顿第一定律（惯性定律）：物体在没有外力作用下，保持静止或匀速直线运动状态。", "keywords": ["牛顿", "惯性", "力学"]},
            {"id": "sci_002", "topic": "牛顿第二定律", "content": "牛顿第二定律：F=ma，力等于质量乘以加速度。", "keywords": ["牛顿", "F=ma", "力学"]},
            {"id": "sci_003", "topic": "牛顿第三定律", "content": "牛顿第三定律：作用力与反作用力大小相等、方向相反。", "keywords": ["牛顿", "作用力", "反作用力"]},
            {"id": "sci_004", "topic": "万有引力定律", "content": "万有引力定律：任何两个物体之间都存在引力，引力大小与质量成正比，与距离平方成反比。", "keywords": ["万有引力", "牛顿", "引力"]},
            {"id": "sci_005", "topic": "相对论", "content": "爱因斯坦相对论包括狭义相对论和广义相对论，E=mc²是狭义相对论的著名公式。", "keywords": ["相对论", "爱因斯坦", "E=mc²"]},
            {"id": "sci_006", "topic": "量子力学", "content": "量子力学是研究微观粒子运动规律的物理学分支，海森堡不确定性原理是其重要原理。", "keywords": ["量子力学", "微观", "不确定性原理"]},
            {"id": "sci_007", "topic": "光速", "content": "光速是宇宙中最快的速度，约为30万公里/秒，是相对论的重要常数。", "keywords": ["光速", "相对论", "宇宙"]},
            {"id": "sci_008", "topic": "能量守恒定律", "content": "能量守恒定律：能量既不会凭空产生，也不会凭空消失，只能从一种形式转化为另一种形式。", "keywords": ["能量守恒", "热力学", "物理"]},
            
            # 化学
            {"id": "sci_009", "topic": "元素周期表", "content": "元素周期表由门捷列夫创立，按原子序数排列所有化学元素。", "keywords": ["元素周期表", "门捷列夫", "化学"]},
            {"id": "sci_010", "topic": "原子结构", "content": "原子由原子核（质子和中子）和核外电子组成。", "keywords": ["原子", "质子", "中子", "电子"]},
            {"id": "sci_011", "topic": "化学键", "content": "化学键包括离子键、共价键和金属键，是原子之间的连接方式。", "keywords": ["化学键", "离子键", "共价键"]},
            {"id": "sci_012", "topic": "氧化还原反应", "content": "氧化还原反应是电子转移的化学反应，氧化剂得电子，还原剂失电子。", "keywords": ["氧化还原", "电子转移", "化学反应"]},
            {"id": "sci_013", "topic": "酸碱中和", "content": "酸碱中和反应是酸和碱反应生成盐和水的过程。", "keywords": ["酸碱", "中和", "化学反应"]},
            {"id": "sci_014", "topic": "有机化学", "content": "有机化学研究含碳化合物的结构、性质和反应。", "keywords": ["有机化学", "碳", "化合物"]},
            
            # 生物学
            {"id": "sci_015", "topic": "细胞", "content": "细胞是生物体的基本结构和功能单位，由细胞膜、细胞质和细胞核组成。", "keywords": ["细胞", "细胞膜", "细胞核"]},
            {"id": "sci_016", "topic": "DNA", "content": "DNA（脱氧核糖核酸）是携带遗传信息的分子，双螺旋结构由沃森和克里克发现。", "keywords": ["DNA", "遗传", "双螺旋"]},
            {"id": "sci_017", "topic": "光合作用", "content": "光合作用是植物利用光能将二氧化碳和水转化为有机物和氧气的过程。", "keywords": ["光合作用", "植物", "氧气"]},
            {"id": "sci_018", "topic": "进化论", "content": "进化论由达尔文提出，认为物种通过自然选择逐渐进化。", "keywords": ["进化论", "达尔文", "自然选择"]},
            {"id": "sci_019", "topic": "生态系统", "content": "生态系统是生物群落与其环境相互作用的系统，包括生产者、消费者和分解者。", "keywords": ["生态系统", "生物群落", "环境"]},
            {"id": "sci_020", "topic": "人体器官", "content": "人体主要器官包括心脏、肺、肝脏、肾脏、大脑等，各司其职维持生命活动。", "keywords": ["器官", "心脏", "大脑", "人体"]},
            
            # 天文学
            {"id": "sci_021", "topic": "太阳系", "content": "太阳系包括太阳和围绕其运行的八大行星、矮行星、小行星等天体。", "keywords": ["太阳系", "行星", "太阳"]},
            {"id": "sci_022", "topic": "银河系", "content": "银河系是太阳系所在的星系，包含约2000亿颗恒星。", "keywords": ["银河系", "星系", "恒星"]},
            {"id": "sci_023", "topic": "黑洞", "content": "黑洞是时空曲率大到光都无法从其事件视界逃脱的天体。", "keywords": ["黑洞", "事件视界", "引力"]},
            {"id": "sci_024", "topic": "宇宙大爆炸", "content": "宇宙大爆炸理论认为宇宙起源于约138亿年前的一个奇点。", "keywords": ["大爆炸", "宇宙", "奇点"]},
            {"id": "sci_025", "topic": "光年", "content": "光年是距离单位，表示光在真空中一年所走的距离，约9.46万亿公里。", "keywords": ["光年", "距离", "光速"]},
            
            # 地球科学
            {"id": "sci_026", "topic": "板块构造", "content": "地球表面由多个板块组成，板块运动导致地震、火山等地质现象。", "keywords": ["板块构造", "地震", "火山"]},
            {"id": "sci_027", "topic": "大气层", "content": "地球大气层分为对流层、平流层、中间层、热层和外逸层。", "keywords": ["大气层", "对流层", "平流层"]},
            {"id": "sci_028", "topic": "水循环", "content": "水循环是水在地球表面、大气和地下之间的循环过程。", "keywords": ["水循环", "蒸发", "降水"]},
            {"id": "sci_029", "topic": "温室效应", "content": "温室效应是大气中温室气体吸收地表辐射导致地球升温的现象。", "keywords": ["温室效应", "二氧化碳", "全球变暖"]},
            {"id": "sci_030", "topic": "臭氧层", "content": "臭氧层位于平流层，能吸收紫外线，保护地球生物。", "keywords": ["臭氧层", "紫外线", "保护"]},
        ]
        
        for item in science_data:
            record = KnowledgeRecord(
                id=item["id"],
                category="科学",
                topic=item["topic"],
                content=item["content"],
                keywords=item["keywords"],
                metadata={"category": "科学"}
            )
            self.records.append(record)
    
    def query(self, query_text: str, category: Optional[str] = None, top_k: int = 5) -> List[Dict]:
        """
        查询知识库
        
        Args:
            query_text: 查询文本
            category: 知识类别过滤（历史、地理、科学）
            top_k: 返回结果数量
        
        Returns:
            匹配的知识记录列表
        """
        if not self._loaded:
            self.load()
        
        results = []
        query_lower = query_text.lower()
        
        for record in self.records:
            # 类别过滤
            if category and record.category != category:
                continue
            
            # 计算匹配分数
            score = 0
            
            # 主题匹配
            if query_lower in record.topic.lower():
                score += 10
            
            # 关键词匹配
            for keyword in record.keywords:
                if query_lower in keyword.lower() or keyword.lower() in query_lower:
                    score += 5
            
            # 内容匹配
            if query_lower in record.content.lower():
                score += 2
            
            if score > 0:
                results.append({
                    "id": record.id,
                    "category": record.category,
                    "topic": record.topic,
                    "content": record.content,
                    "keywords": record.keywords,
                    "score": score
                })
        
        # 按分数排序
        results.sort(key=lambda x: x["score"], reverse=True)
        
        return results[:top_k]
    
    def check_fact(self, text: str, category: Optional[str] = None) -> List[Dict]:
        """
        检查文本中的常识性错误
        
        Args:
            text: 待检查文本
            category: 知识类别过滤
        
        Returns:
            可能的错误列表
        """
        if not self._loaded:
            self.load()
        
        errors = []
        text_lower = text.lower()
        
        # 检查历史错误
        if category is None or category == "历史":
            errors.extend(self._check_history_errors(text, text_lower))
        
        # 检查地理错误
        if category is None or category == "地理":
            errors.extend(self._check_geography_errors(text, text_lower))
        
        # 检查科学错误
        if category is None or category == "科学":
            errors.extend(self._check_science_errors(text, text_lower))
        
        return errors
    
    def _check_history_errors(self, text: str, text_lower: str) -> List[Dict]:
        """检查历史错误"""
        errors = []
        
        # 检查朝代时间错误
        dynasty_checks = [
            ("秦朝", ["前221年", "前207年"], ["秦始皇", "嬴政"]),
            ("汉朝", ["前202年", "220年"], ["刘邦", "汉武帝"]),
            ("唐朝", ["618年", "907年"], ["李世民", "唐太宗"]),
            ("宋朝", ["960年", "1279年"], ["赵匡胤"]),
            ("明朝", ["1368年", "1644年"], ["朱元璋"]),
            ("清朝", ["1636年", "1912年"], ["康熙", "乾隆"]),
        ]
        
        for dynasty, dates, figures in dynasty_checks:
            if dynasty in text:
                # 检查相关人物是否匹配正确朝代
                for figure in figures:
                    if figure in text:
                        # 简单检查：如果同时出现其他朝代人物，可能有错误
                        for other_dynasty, _, other_figures in dynasty_checks:
                            if other_dynasty != dynasty:
                                for other_figure in other_figures:
                                    if other_figure in text:
                                        errors.append({
                                            "type": "历史",
                                            "severity": "high",
                                            "description": f"可能的朝代混淆：{dynasty}和{other_dynasty}的人物同时出现",
                                            "suggestion": f"请确认{figure}和{other_figure}是否属于同一时期"
                                        })
        
        return errors
    
    def _check_geography_errors(self, text: str, text_lower: str) -> List[Dict]:
        """检查地理错误"""
        errors = []
        
        # 检查河流位置错误
        river_checks = [
            ("长江", ["中国", "亚洲"], ["美国", "欧洲", "非洲"]),
            ("黄河", ["中国", "亚洲"], ["美国", "欧洲", "非洲"]),
            ("亚马逊河", ["南美洲", "巴西"], ["非洲", "亚洲"]),
            ("尼罗河", ["非洲", "埃及"], ["亚洲", "欧洲"]),
        ]
        
        for river, correct_locations, wrong_locations in river_checks:
            if river in text:
                for wrong_loc in wrong_locations:
                    if wrong_loc in text:
                        errors.append({
                            "type": "地理",
                            "severity": "high",
                            "description": f"可能的地理错误：{river}不在{wrong_loc}",
                            "suggestion": f"{river}位于{correct_locations[0]}"
                        })
        
        return errors
    
    def _check_science_errors(self, text: str, text_lower: str) -> List[Dict]:
        """检查科学错误"""
        errors = []
        
        # 检查常见科学误解
        misconceptions = [
            ("真空不能传声", ["声音在真空中传播"], "声音不能在真空中传播"),
            ("光速最快", ["超光速", "比光速快"], "根据相对论，光速是宇宙中最快的速度"),
            ("进化论", ["人是猴子变的"], "人类和猴子有共同祖先，不是猴子直接进化而来"),
        ]
        
        for correct, wrong_phrases, correction in misconceptions:
            for wrong_phrase in wrong_phrases:
                if wrong_phrase in text:
                    errors.append({
                        "type": "科学",
                        "severity": "medium",
                        "description": f"可能的科学错误：{wrong_phrase}",
                        "suggestion": correction
                    })
        
        return errors


# 全局实例
_knowledge_loader: Optional[KnowledgeLoader] = None


def load_knowledge() -> KnowledgeLoader:
    """
    加载知识库（单例模式）
    
    Returns:
        知识库加载器实例
    """
    global _knowledge_loader
    if _knowledge_loader is None:
        _knowledge_loader = KnowledgeLoader()
        _knowledge_loader.load()
    return _knowledge_loader
