import click

from winner_of_day.bot.bot import run_bot


@click.command()
@click.option("--storage", type=click.Path(), required=True, help="Path to the storage location.")
@click.option("--token", type=str, required=True, help="Authentication token.")
@click.option("--admin_id", type=int, required=True, help="Administrator id.")
@click.option("--gpt_api", type=str, required=True, help="Gpt api key.")
@click.option("--suno_endpoint", type=str, required=True, help="Suno endpoint url.")
def main(storage: str, token: str, admin_id: int, gpt_api:str, suno_endpoint: str):
    run_bot(token, admin_id, storage, gpt_api, suno_endpoint)

main()
