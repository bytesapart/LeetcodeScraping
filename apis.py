from typing import List

import urls
from session import LeetCodeSession
from models import Problem, ProblemDetail


class LeetCodeClient(LeetCodeSession):
    def get_problems(self) -> List[Problem]:
        r = self.s.get(urls.PROBLEMS)
        try:
            a = r.json()["stat_status_pairs"]
            return [Problem(d) for d in a]
        except:
            return []

    def get_problem_detail(self, question_slug: str) -> ProblemDetail:
        csrf = self.s.cookies.get("csrftoken")
        body = """{"query":"query getQuestionDetail($titleSlug: String!) {\\n  question(titleSlug: $titleSlug) {\\n    questionId\\n    questionTitle\\n    content\\n    difficulty\\n    stats\\n    similarQuestions\\n    libraryUrl\\n    mysqlSchemas\\n    randomQuestionUrl\\n    sessionId\\n    categoryTitle\\n    submitUrl\\n    interpretUrl\\n    codeDefinition\\n    sampleTestCase\\n    enableTestMode\\n    metaData\\n    enableRunCode\\n    enableSubmit\\n    judgerAvailable\\n    infoVerified\\n    envInfo\\n    urlManager\\n    article\\n    questionDetailUrl\\n    isLiked\\n    nextChallengePairs\\n    __typename\\n  }}\\n","variables":{"titleSlug":"%s"},"operationName":"getQuestionDetail"}""" % question_slug
        # body = """{"query":"query getQuestionDetail($titleSlug: String!) {\\n  question(titleSlug: $titleSlug) {\\n    questionId\\n    questionTitle\\n    content\\n    difficulty\\n    stats\\n    contributors\\n    companyTags\\n    topicTags\\n    similarQuestions\\n    discussUrl\\n    libraryUrl\\n    mysqlSchemas\\n    randomQuestionUrl\\n    sessionId\\n    categoryTitle\\n    submitUrl\\n    interpretUrl\\n    codeDefinition\\n    sampleTestCase\\n    enableTestMode\\n    metaData\\n    enableRunCode\\n    enableSubmit\\n    judgerAvailable\\n    emailVerified\\n    envInfo\\n    urlManager\\n    likesDislikes {\\n      likes\\n      dislikes\\n      __typename\\n    }\\n    article\\n    questionDetailUrl\\n    isLiked\\n    discussCategoryId\\n    nextChallengePairs\\n    __typename\\n  }}\\n","variables":{"titleSlug":"%s"},"operationName":"getQuestionDetail"}""" % question_slug
        r = self.s.post(urls.GRAPHQL,
                        data=body,
                        headers={"referer": urls.DESCRIPTION % question_slug,
                                 "X-CSRFToken": csrf,
                                 "Content-Type": "application/json"})
        d = {}
        try:
            d = r.json()["data"]["question"]
        except:
            pass
        return ProblemDetail(d or {})
