import traceback

async def safe_slash(interaction, func, *args, ephemeral=True):
    """
    Universal wrapper:
    - auto defer
    - safe execution
    - auto followup response
    """

    try:
        # 💥 автоматически предотвращаем timeout
        await interaction.response.defer(ephemeral=ephemeral)

        # выполняем логику
        result = await func(*args)

        # если функция что-то вернула — отправляем
        if result:
            await interaction.followup.send(result, ephemeral=ephemeral)

    except Exception as e:
        traceback.print_exc()
        try:
            await interaction.followup.send("❌ Ошибка выполнения команды", ephemeral=ephemeral)
        except:
            pass
