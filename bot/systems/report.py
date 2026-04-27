reports = []


def create_report(reporter, target, reason):
    report = {
        "reporter": reporter,
        "target": target,
        "reason": reason
    }

    reports.append(report)
    return report
