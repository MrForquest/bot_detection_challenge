import numpy as np
import pandas as pd
from .ua_parser import parse_ua


def prepare_events(ev, meta):
    ev = ev.drop_duplicates(keep="first")

    ev = ev.merge(
        meta[["cookie_id", "window_start_ts", "window_end_ts"]], on="cookie_id"
    )
    ev = ev[(ev.event_ts >= ev.window_start_ts) & (ev.event_ts < ev.window_end_ts)]
    ev["platform"] = (
        ev["platform"].str.lower().replace({"web": "desktop", "iphone": "ios"})
    )
    ev = ev[ev["event_name"] != "captcha_shown"]
    uniq = ev["user_agent"].drop_duplicates()
    ua_parsed = pd.DataFrame([parse_ua(u) for u in uniq], index=uniq)
    ev = ev.join(ua_parsed, on="user_agent")

    return ev


def cookie_features(session_events):
    session_events = session_events.sort_values("event_ts")
    ptr = session_events[["pointer_x", "pointer_y"]].dropna()
    n = len(session_events)
    if n == 0:
        raise ValueError("The number of sessions must be greater than zero")

    session_features = {
        "n_ua": session_events["user_agent"].nunique(),
        "n_ua_os": session_events["ua_os"].nunique(),
        "n_ua_browser": session_events["ua_browser"].nunique(),
        "platform": session_events["platform"].iloc[0],
        "ua_os": session_events["ua_os"].iloc[0],
        "ua_browser": session_events["ua_browser"].iloc[0],
        "ua_device": session_events["ua_device"].iloc[0],
        "ua_kind": session_events["ua_kind"].iloc[0],
        "max_page": session_events["search_page"].max(),
        "mean_page": session_events["search_page"].mean(),
        "ptr_std_x": ptr["pointer_x"].std(),
        "ptr_std_y": ptr["pointer_y"].std(),
        "ptr_mean_x": ptr["pointer_x"].mean(),
        "ptr_mean_y": ptr["pointer_y"].mean(),
        "ptr_range_x": ptr["pointer_x"].max() - ptr["pointer_x"].min(),
        "ptr_range_y": ptr["pointer_y"].max() - ptr["pointer_y"].min(),
        "n_item_id": session_events["item_id"].nunique(),
        "ratio_loc": session_events["item_location"].nunique() / n,
        "ratio_cat": session_events["item_category"].nunique() / n,
        "n_pointer_points": len(ptr),
        "n_events": n,
    }
    event_names = [
        "item_view",
        "search_results_view",
        "photo_swipe",
        "favorite_add",
        "seller_page_view",
        "contact_phone_show",
        "login",
        "contact_chat_open",
        "contact_message_sent",
    ]
    for col in event_names:
        session_features[f"ratio_ev_{col}"] = (
            session_events["event_name"] == col
        ).sum() / n
    dt = session_events["event_ts"].diff().dt.total_seconds().dropna()
    mean = dt.mean()
    dt_features = {
        "dt_median": dt.median(),
        "dt_std": dt.std(),
        "dt_max": dt.max(),
        "dt_min": dt.min(),
        "dt_cv": dt.std() / mean if n > 2 and mean > 0 else np.nan,  # нерегулярность
    }
    session_features.update(dt_features)

    return session_features


def generate_features(events, meta):
    ev = prepare_events(events, meta)
    rows = {cid: cookie_features(se) for cid, se in ev.groupby("cookie_id", sort=False)}
    features = pd.DataFrame.from_dict(rows, orient="index").reindex(meta.cookie_id)
    features["cookie_age_days"] = (
        meta.window_start_ts - meta.cookie_created_at
    ).dt.total_seconds().values / 86400
    # features = features.fillna(-1)

    return features
