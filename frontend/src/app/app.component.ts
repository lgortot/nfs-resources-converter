import { ApplicationRef, ChangeDetectionStrategy, ChangeDetectorRef, Component } from '@angular/core';
import { EelDelegateService } from './services/eel-delegate.service';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MainService } from './services/main.service';
import { MatDialog } from '@angular/material/dialog';
import { ConfirmDialogComponent } from './components/confirm.dialog/confirm.dialog.component';
import { firstValueFrom } from 'rxjs';
import {
  RunCustomActionDialogComponent
} from './components/run-custom-action.dialog/run-custom-action.dialog.component';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class AppComponent {

  constructor(readonly eelDelegate: EelDelegateService,
              readonly mainService: MainService,
              readonly dialog: MatDialog,
              private readonly snackBar: MatSnackBar,
              private readonly cdr: ChangeDetectorRef,
              private readonly appRef: ApplicationRef) {
  }

  async saveResource() {
    try {
      const changes = Object.entries(this.mainService.changedDataBlocks).filter(([id, _]) => id != '__has_external_changes__');
      await this.eelDelegate.saveFile(changes.map(([id, value]) => {
        return { id, value };
      }));
      this.mainService.clearUnsavedChanges();
      this.snackBar.open('File Saved!', 'OK', { duration: 1500 });
    } catch (err: any) {
      this.snackBar.open('Error while saving file! ' + err.errorText, 'OK :(', { duration: 5000 });
    }
  }

  async reloadResource() {
    if (this.mainService.hasUnsavedChanges) {
      let dialogRef = this.dialog.open(ConfirmDialogComponent, {
        data: { text: 'There are unsaved changes, which will be lost. Are you sure you want to reload file?' }
      });
      if (!(await firstValueFrom(dialogRef.afterClosed()))) {
        return;
      }
    }
    const path = this.mainService.eelDelegate.openedResourcePath$.getValue();
    if (path) {
      this.eelDelegate.openFile(path, true).then();
    }
    this.cdr.markForCheck();
  }

  async runCustomAction(action: CustomAction) {
    if (this.mainService.hasUnsavedChanges) {
      let dialogRef = this.dialog.open(ConfirmDialogComponent, {
        data: { text: 'Cannot run custom action on a file with not saved changes. Do you want to save them first?' }
      });
      if (!(await firstValueFrom(dialogRef.afterClosed()))) {
        return;
      }
      await this.saveResource();
    }
    let dialogRef = this.dialog.open(RunCustomActionDialogComponent, {
      data: action
    });
    const args: any[] | undefined = await firstValueFrom(dialogRef.afterClosed());
    if (!args) {
      return;
    }
    try {
      await this.mainService.runCustomAction(action, args);
      this.snackBar.open('Action performed!', 'OK', { duration: 1500 });
    } catch (err: any) {
      this.mainService.clearUnsavedChanges();
      this.reloadResource().then();
      this.snackBar.open('Error while performing action! Reverting file state.. ' + err.errorText || err, 'OK :(', { duration: 5000 });
    }
  }

}
