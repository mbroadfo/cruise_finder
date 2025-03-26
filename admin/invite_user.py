import click
from auth0_invite import invite_user

@click.command()
@click.argument("email")
def main(email):
    """Invite a user to the Cruise Viewer app."""
    click.echo(f"\nYou're about to invite: {click.style(email, fg='cyan')}")
    if click.confirm("Continue?", default=True):
        try:
            result = invite_user(email)
            click.secho("✅ Invitation sent!", fg="green")
            click.echo(result)
        except Exception as e:
            click.secho(f"❌ Failed to invite user: {str(e)}", fg="red")

if __name__ == "__main__":
    main()
