import sys
from typing import Optional, NoReturn

import curator
from elasticsearch import Elasticsearch, RequestsHttpConnection
from slacker import Slacker


class ElasticSearchCurator:
    SLACK_CHANNEL = "#es-curator-noti"
    SLACK_BOT_NAME = "ElasticSearch Curator"

    def __init__(self):
        self.es = Elasticsearch(
            hosts=[{"host": "host", "port": 443}],
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )
        self.slack = Slacker("slack-token")

    def execute(self, index_prefix: str, month_period: int) -> Optional[NoReturn]:
        try:
            indexes = curator.IndexList(self.es)
        except:
            self._to_slack(
                channel=self.SLACK_CHANNEL,
                text=f">*Exception Occured*\n>{sys.exc_info()}",
                bot_name=self.SLACK_BOT_NAME,
            )
            raise Exception("IndexList exception")

        indexes.filter_by_regex(
            kind="prefix", value=index_prefix,
        )
        indexes.filter_by_age(
            source="name",
            direction="older",
            timestring="%Y.%m.%d",
            unit="months",
            unit_count=month_period,
        )
        deleted_count = len(indexes.indices)

        if deleted_count != 0:
            curator.DeleteIndices(indexes).do_action()

        self._to_slack(
            channel=self.SLACK_CHANNEL,
            text=f">*Index*\n>{index_prefix}\n>*Count*\n>{deleted_count}\n>*Period*\n>{month_period}",
            bot_name=self.SLACK_BOT_NAME,
        )

    def _to_slack(self, channel: str, text: str, bot_name: str) -> None:
        self.slack.chat.post_message(
            channel=channel, text=text, username=bot_name,
        )


def run():
    es = ElasticSearchCurator()
    es.execute(index_prefix="alblogs", month_period=3)
