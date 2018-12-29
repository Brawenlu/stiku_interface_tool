import random
from util.domain_mgr import DomainMgr
from util.http_util import HttpConnectMgr
from service.problem_service import ProblemService
from util.file_util import FileUtil
from util.file_util import IniUtil

class WeekTestUtil:
    def __init__(self):
        pass

    @staticmethod
    def get_answer_picture():
        pics = ["http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_103571_2_1463990372676",
                "http://7xpnsw.com1.z0.glb.clouddn.com/F_w_t_p_105616_2",
                "http://7xpnsw.com1.z0.glb.clouddn.com/F_w_t_p_105620_2",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77084_2_1463898052734",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77091_4_1464084865156",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77152_4_1463896815066",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77184_2_1463902113410",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77254_2_1749851801",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77273_2_1466576253394"]

        if random.randint(0,1) == 0:
            rand_pic_index = random.randint(0,len(pics)-1)
            return pics[rand_pic_index]
        else:
            rand_num1 = random.randint(0, (len(pics)-1))
            temp = [i for i in range(len(pics))]
            temp.remove(rand_num1)
            rand_num2 = temp[random.randint(0,(len(temp)-1))]
            return pics[rand_num1] + "," + pics[rand_num2]

    @staticmethod
    def post_answer_pictures(week_test_problem_id):
        host = DomainMgr.get_domain("student_host")
        http_util = HttpConnectMgr.get_http_connect()
        pics = ["http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_103571_2_1463990372676",
                "http://7xpnsw.com1.z0.glb.clouddn.com/F_w_t_p_105616_2",
                "http://7xpnsw.com1.z0.glb.clouddn.com/F_w_t_p_105620_2",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77084_2_1463898052734",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77091_4_1464084865156",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77152_4_1463896815066",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77184_2_1463902113410",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77254_2_1749851801",
                "http://7xpnsw.com1.z0.glb.clouddn.com/w_t_p_77273_2_1466576253394"]
        pic_params = dict()
        pic_params["wtpId"] = week_test_problem_id
        if random.randint(0,1) == 0:
            rand_pic_index = random.randint(0,len(pics)-1)
            pic_params["picPath"] = pics[rand_pic_index]
        else:
            rand_num1 = random.randint(0, (len(pics)-1))
            temp = [i for i in range(len(pics))]
            temp.remove(rand_num1)
            rand_num2 = temp[random.randint(0,(len(temp)-1))]
            pic_params["picPath"] = pics[rand_num1] + "," + pics[rand_num2]
        res = http_util.post(host,"/web-student/weekTest/submitPic", pic_params)

    @staticmethod
    def get_xz_count(week_test_id, problem_count):
        problem_service = ProblemService()
        xz_count = 0
        for problem_index in range(problem_count):
            paper_problem_id = problem_service.get_week_test_paper_problem_id(week_test_id,problem_index+1)
            problem_type = problem_service.get_problem_type_by_id(paper_problem_id)
            if problem_type == 0:
                xz_count += 1
        return xz_count

    @staticmethod
    def get_app_strategy_answer_list(student_level, problem_count, xz_count):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
        level = "level_"+str(student_level)
        xz_dividing_rate = float(ini_util.get_item_attr(level, "xz_dividing_rate"))
        xz_high_score_rate = float(ini_util.get_item_attr(level, "xz_high_score_rate"))
        xz_low_score_rate = float(ini_util.get_item_attr(level, "xz_low_score_rate"))
        jd_dividing_rate = float(ini_util.get_item_attr(level, "jd_dividing_rate"))
        jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
        jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
        answer_list = [0] * problem_count
        other_count = problem_count - xz_count
        for index in range(xz_count):
            if index < xz_dividing_rate * xz_count:
                if random.random() < xz_high_score_rate:
                    answer_list[index] = 1
            else:
                if random.random() < xz_low_score_rate:
                    answer_list[index] = 1
        for index2 in range(xz_count, problem_count):
            if (index2-xz_count) < jd_dividing_rate * other_count:
                if random.random() < jd_high_score_rate:
                    answer_list[index2] = 1
            else:
                if random.random() < jd_low_score_rate:
                    answer_list[index2] = 1
        return answer_list

    @staticmethod
    def get_strategy_answer_list(week_test_id, student_level, problem_count):
        root_dir = FileUtil.get_app_root_dir()
        ini_util = IniUtil(root_dir + "/student/feedback_strategy.ini")
        level = "level_"+str(student_level)
        xz_dividing_rate = float(ini_util.get_item_attr(level, "xz_dividing_rate"))
        xz_high_score_rate = float(ini_util.get_item_attr(level, "xz_high_score_rate"))
        xz_low_score_rate = float(ini_util.get_item_attr(level, "xz_low_score_rate"))
        jd_dividing_rate = float(ini_util.get_item_attr(level, "jd_dividing_rate"))
        jd_high_score_rate = float(ini_util.get_item_attr(level, "jd_high_score_rate"))
        jd_low_score_rate = float(ini_util.get_item_attr(level, "jd_low_score_rate"))
        answer_list = [0] * problem_count
        xz_count = WeekTestUtil.get_xz_count(week_test_id, problem_count)
        other_count = problem_count - xz_count
        for index in range(xz_count):
            if index < xz_dividing_rate * xz_count:
                if random.random() < xz_high_score_rate:
                    answer_list[index] = 1
            else:
                if random.random() < xz_low_score_rate:
                    answer_list[index] = 1
        for index2 in range(xz_count, problem_count):
            if (index2-xz_count) < jd_dividing_rate * other_count:
                if random.random() < jd_high_score_rate:
                    answer_list[index2] = 1
            else:
                if random.random() < jd_low_score_rate:
                    answer_list[index2] = 1
        return answer_list