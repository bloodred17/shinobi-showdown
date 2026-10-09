import { expect, test } from '@playwright/test';

test('two browser clients load the WASM host and connect independently', async ({
  browser,
}) => {
  const firstContext = await browser.newContext();
  const secondContext = await browser.newContext();
  const firstPlayer = await firstContext.newPage();
  const secondPlayer = await secondContext.newPage();

  await Promise.all([firstPlayer.goto('/'), secondPlayer.goto('/')]);
  await expect(firstPlayer.getByRole('heading', { level: 1 })).toHaveText(
    'Shinobi Tactics',
  );
  await expect(secondPlayer.locator('#shinobi-game')).toBeVisible();

  await Promise.all([
    firstPlayer.getByRole('button', { name: 'Connect' }).click(),
    secondPlayer.getByRole('button', { name: 'Connect' }).click(),
  ]);
  await expect(firstPlayer.getByTestId('server-state')).toHaveText('connected');
  await expect(secondPlayer.getByTestId('server-state')).toHaveText(
    'connected',
  );
  await expect(firstPlayer.getByTestId('last-server-event')).toHaveText(
    'connected',
  );

  await firstPlayer.getByRole('button', { name: 'Load battlefield' }).click();
  await expect(firstPlayer.getByTestId('battlefield-state')).toHaveCount(0);

  await Promise.all([firstContext.close(), secondContext.close()]);
});
