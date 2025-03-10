import { Injectable, NgZone } from '@angular/core';
import { BehaviorSubject } from 'rxjs';

declare const eel: { expose: (func: Function, alias: string) => void } & { [key: string]: Function };

@Injectable({
  providedIn: 'root'
})
export class EelDelegateService {

  public readonly openedResource$: BehaviorSubject<ReadData | ReadError | null> = new BehaviorSubject<ReadData | ReadError | null>(null);
  public readonly openedResourcePath$: BehaviorSubject<string | null> = new BehaviorSubject<string | null>(null);

  constructor(
    private readonly ngZone: NgZone,
  ) {
    eel.expose(this.wrapHandler(this.openFile), 'open_file');
    eel['on_angular_ready']();
  }

  private wrapHandler(handler: (...args: any[]) => unknown) {
    return ((...args: any[]) => {
      try {
        NgZone.assertInAngularZone();
        handler.bind(this)(...args);
      } catch (err) {
        this.ngZone.run(handler, this, args);
      }
    });
  }

  public async openFile(path: string, forceReload: boolean = false) {
    this.openedResource$.next(null);
    this.openedResourcePath$.next(null);
    const res: ReadData | ReadError = await eel['open_file'](path, forceReload)();
    this.openedResource$.next(res);
    this.openedResourcePath$.next(path);
  }

  public async openFileWithSystemApp(path: string) {
    await eel['open_file_with_system_app'](path)();
  }

  public async runCustomAction(readData: ReadData, action: CustomAction, args: { [key: string]: any }) {
    return eel['run_custom_action'](readData.block_id, action, args)();
  }

  public async saveFile(changes: {id: string, value: any}[]) {
    return eel['save_file'](this.openedResourcePath$.getValue(), changes)();
  }

  public async serializeResource(id: string, settingsPatch: any = {}): Promise<string[]> {
    return eel['serialize_resource'](id, settingsPatch)();
  }

  public async serializeResourceTmp(id: string, changes: {id: string, value: any}[], settingsPatch: any = {}): Promise<string[]> {
    return eel['serialize_resource_tmp'](id, changes, settingsPatch)();
  }

  public async deserializeResource(id: string): Promise<ReadData | ReadError> {
    return eel['deserialize_resource'](id)();
  }
}
