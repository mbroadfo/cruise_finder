import click
from auth0_utils import get_m2m_token, create_user, send_password_reset_email

@click.command()
def invite_user():
    email = click.prompt("📧 Email address", type=str)
    given_name = click.prompt("🧑 Given name", type=str)
    family_name = click.prompt("👪 Family name", type=str)

    click.echo("\n🔍 Review the information:")
    click.echo(f"   Email       : {email}")
    click.echo(f"   Given name  : {given_name}")
    click.echo(f"   Family name : {family_name}")

    if not click.confirm("\n✅ Proceed with invitation?"):
        click.echo("❌ Cancelled.")
        return

    click.echo("\n🔐 Requesting token...")
    token = get_m2m_token()

    click.echo("📨 Creating user...")
    user = create_user(email, given_name, family_name, token)
    
    click.echo("📨 Sending Invitation...")
    send_password_reset_email(email, token)

    click.echo("\n✅ Invitation sent successfully!")
    click.echo(f"   User ID: {user.get('user_id')}")
