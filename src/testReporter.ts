import { DefaultReporter } from 'vitest/reporters';

// BaseReporter isn't exported as a runtime value, so pull it from the prototype chain

const BaseReporter = Object.getPrototypeOf(DefaultReporter);

export default class SummaryOnlyReporter extends BaseReporter {
  printTestModule(): void {}
}
