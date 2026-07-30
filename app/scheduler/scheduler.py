from datetime import date as date_type
from datetime import timedelta
from  app.db.crud import get_all_users, get_transactions, get_active_budgets, get_all_active_budgets, get_budget_status, has_notification, create_notification, get_category_summary, get_total_expenses
from app.db.session import AsyncSessionLocal
import asyncio
from app.notifications.email_sender import send_email

async def run_daily_check():
    today = date_type.today()
    async with AsyncSessionLocal() as session:
        users = await get_all_users(session)
        for user in users:
            try:
                transactions = await get_transactions(
                    session,
                    user_id=user.id,
                    date_from=today,
                    date_to=today,
                )
                if not transactions:
                    message = "You haven't logged anything today. Don't forget to record any spending or income!"
                else:
                    message = f"You logged {len(transactions)} transaction(s) today:\n" + "\n".join(str(t) for t in transactions)

                if user.email:
                    send_email(user.email, subject="Transactions Log Update", body=message)
                else:
                    print(f"User {user.id} has no email on file, skipping.")
            except Exception as e:
                print(f"Failed for user {user.id}: {e}")
            
            await check_budget_milestones(session, user)
            await check_remaining_budget_days(session, user)
            await no_spending_streak(session, user)
            await unusual_spending_detection(session, user)
            await weekly_summary(session, user)

async def check_budget_milestones(session, user):
    budgets = await get_all_active_budgets(session, user.id)
    for budget in budgets:
        try:
            status = await get_budget_status(session, user.id, budget.category)
            for milestone in [90, 75, 50, 25]:
                if status['percentage_used'] >= milestone:
                    notification_type = f"budget_milestone_{milestone}"
                    already_sent = await has_notification(session, user.id, notification_type, reference_id=budget.id)
                    if already_sent:
                        break
                    
                    message = f"You have spent {status['percentage_used']:.1f}% of your budget"
                    if user.email:
                        send_email(user.email, subject=f"Budget Milestone - {status['percentage_used']:.1f}% used", body=message)
                        await create_notification(
                            session,
                            user_id=user.id,
                            notification_type=f"budget_milestone_{milestone}",
                            reference_id=budget.id
                            )
                    break
        except Exception as e:
            print(f"Failed for budget {budget.id}: {e}")

async def check_remaining_budget_days(session, user):
    budgets = await get_all_active_budgets(session, user.id)
    for budget in budgets:
        try:
            status = await get_budget_status(session, user.id, budget.category)
            days_remaining = (budget.end_date - date_type.today()).days
            if days_remaining < 3 and status['percentage_used'] < 50:
                notification_type = "spend_freely"
                already_sent = await has_notification(session, user.id, notification_type, reference_id=budget.id)
                if already_sent:
                    continue
                message = f"You have {days_remaining} day(s) remaining before your budget ends.and you have only spent {status['percentage_used']}% of it. You can spend freely and enjoy the rest of your budget unless you plan to save."
                if user.email:
                    send_email(user.email, subject=f"Remaining Budget - {100 - status['percentage_used']}% left.", body=message)
                    await create_notification(
                        session,
                        user_id=user.id,
                        notification_type=notification_type,
                        reference_id=budget.id
                        )
        except Exception as e:
                    print(f"Failed for budget {budget.id}: {e}")

async def no_spending_streak(session, user):
    most_recent_transaction = await get_transactions(session, user_id=user.id, limit=1)
    if most_recent_transaction:
        streak = (date_type.today() - most_recent_transaction[0].date).days
        is_milestone = streak in (3, 5) or (streak >= 10 and streak % 10 == 0)
        if is_milestone:
            notification_type = f"no_spending_streak_{streak}"
            reference_id = most_recent_transaction[0].id
            already_sent = await has_notification(session, user.id, notification_type, reference_id=reference_id)
            if already_sent:
                return
            message = f"You haven't recorded any expenses for {streak} days. Nice job keeping your spending in check!"
            if user.email:
                send_email(user.email, subject=f"No Spending Streak - {streak} days", body=message)
                await create_notification(
                    session,
                    user_id=user.id,
                    notification_type=notification_type,
                    reference_id=reference_id
                    )

async def unusual_spending_detection(session, user):
    today = date_type.today()
    last_week = today - timedelta(days=7)
    week_start = last_week.isoformat()
    last_4_weeks = today - timedelta(days=35)
    txns_last_week = await get_category_summary(session, user_id=user.id, type='expense', date_from=last_week, date_to=today)
    txns_last_4_weeks = await get_category_summary(session, user_id=user.id, type='expense', date_from=last_4_weeks, date_to=last_week)
    for category, amount in txns_last_week.items():
        current_week = amount
        baseline_total = txns_last_4_weeks.get(category, 0)
        baseline_average = baseline_total / 4
        if baseline_average >= 500 and current_week >= (baseline_average * 1.5):
            percentage_increase = ((current_week - baseline_average) / baseline_average ) * 100
            notification_type = f"unusual_spending_{category}_{week_start}"
            already_sent = await has_notification(session, user.id, notification_type)
            if already_sent:
                continue
            message = f"Your spending on {category.title()} was {percentage_increase:.1f}% higher this week than your usual weekly average (PKR {current_week:.0f} vs PKR {baseline_average:.0f})."
            if user.email:
                send_email(user.email, subject=f"Unusual Spending Detected in {category.title()}", body=message)
                await create_notification(
                    session,
                    user_id=user.id,
                    notification_type=notification_type,
                    )

async def weekly_summary(session, user):
    today = date_type.today()
    week_start = today - timedelta(days=7)
    if today.weekday() == 6:
        total_spent = await get_total_expenses(session, user.id, date_from=week_start, date_to=today)

        category_summary = await get_category_summary(session, user.id, type="expense", date_from=week_start, date_to=today)
        if category_summary:
            top_category = max(category_summary, key=category_summary.get)
            top_amount = category_summary[top_category]
            top_category_text = f"{top_category.title()} — PKR {top_amount:,.0f}"
        else:
            top_category_text = "No spending recorded this week"

        week_transactions = await get_transactions(session, user.id, date_from=week_start, date_to=today, limit=50)
        biggest_transaction = None
        if week_transactions:
            biggest_transaction = max(week_transactions, key=lambda t: t.amount)
            largest_expense = (
                f"PKR {biggest_transaction.amount:,.0f}\n"
                f"Category: {biggest_transaction.category.title()}\n"
                f"Description: {biggest_transaction.description or 'No description'}"
            )
        else:
            largest_expense = "No expenses recorded this week."


        last_week = week_start - timedelta(days=7)
        txns_this_week = category_summary
        txns_last_week = await get_category_summary(session, user_id=user.id, type='expense', date_from=last_week, date_to=week_start)

        total_this_week = sum(txns_this_week.values())
        total_last_week = sum(txns_last_week.values())
        if total_last_week > 0:
            percentage_increase = ((total_this_week - total_last_week) / total_last_week) * 100
            comparison = (
                f"You spent {abs(percentage_increase):.1f}% "
                f"{'more' if percentage_increase >= 0 else 'less'} than last week."
            )
        else:
            comparison = (
                "This is your first week with enough data to compare your spending."
            )

        notification_type = f"weekly_summary_{week_start}"
        already_sent = await has_notification(session, user.id, notification_type)
        if already_sent:
            return
        
        name = user.name or user.username or "there"
        message = f"""
Hi {name},

Here's your spending summary for the past week:

Total spent: PKR {total_spent:,.0f}

Top spending category:
{top_category_text}

Largest expense:
{largest_expense}

Compared to last week:
{comparison}

Keep tracking your spending — you’re building better financial habits every week.

— Nisaab
        """
    if user.email:
            send_email(user.email, subject=f"Your Weekly Financial Summary", body=message)
            await create_notification(
                session,
                user_id=user.id,
                notification_type=notification_type,
                )


asyncio.run(run_daily_check())