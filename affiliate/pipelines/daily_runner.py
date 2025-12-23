from affiliate.core.selector import pick_topN
from affiliate.generate.content import generate_post
from affiliate.publish.wordpress import post_wordpress
from affiliate.publish.line import push_line
from affiliate.publish.slack import notify_slack
from affiliate.publish.notion import log_notion
from affiliate.core.utils import env_int


def main():
    top_n = env_int("TOP_N", 3)
    ranked = pick_topN(top_n=top_n)

    posted_links = []
    lines = []
    for offer, score in ranked:
        post = generate_post(offer, score)

        link = ""
        try:
            link = post_wordpress(post["title"], post["content"])
        except Exception:
            link = ""

        if link:
            posted_links.append(link)

        try:
            log_notion(
                {
                    "name": offer.title,
                    "url": link or offer.url,
                    "final_score": score.final_score,
                    "gross_profit_yen": score.gross_profit_yen,
                    "conv_prob": score.conv_prob,
                }
            )
        except Exception:
            pass

        lines.append(
            f"- {offer.source} | {offer.title}\n"
            f"  score={score.final_score:.0f} 粗利={score.gross_profit_yen:.0f} CV={score.conv_prob*100:.0f}%\n"
            f"  link={link or offer.url}"
        )

    msg = "【本日の上位案件】\n" + "\n".join(lines)

    try:
        push_line(msg)
    except Exception:
        pass
    try:
        notify_slack(msg)
    except Exception:
        pass

    print(msg)
    if posted_links:
        print("Posted:", "\n".join(posted_links))


if __name__ == "__main__":
    main()
