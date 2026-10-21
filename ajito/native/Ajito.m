#import <Cocoa/Cocoa.h>
#import <WebKit/WebKit.h>
#import <UniformTypeIdentifiers/UniformTypeIdentifiers.h>

@interface Ajito : NSObject <NSApplicationDelegate, WKNavigationDelegate, WKUIDelegate, WKScriptMessageHandler, NSWindowDelegate>
@property NSWindow *window;
@property WKWebView *web;
@property NSTask *backend;
@property NSURL *localURL;
@property BOOL quitting;
@property BOOL ready;
@property BOOL operationBusy;
@property NSString *smokePath;
@property NSString *screenshotPath;
@end

@implementation Ajito
- (NSString *)argument:(NSString *)name {
    NSArray *args=NSProcessInfo.processInfo.arguments;NSUInteger i=[args indexOfObject:name];
    return i!=NSNotFound && args.count>i+1 ? args[i+1] : nil;
}
- (void)applicationDidFinishLaunching:(NSNotification *)notification {
    self.smokePath=[self argument:@"--smoke-test"] ?: [self argument:@"--read-check"] ?: [self argument:@"--setup-check"];self.screenshotPath=[self argument:@"--screenshot"];
    NSMenu *menu=[NSMenu new];NSMenuItem *appItem=[NSMenuItem new];[menu addItem:appItem];NSMenu *appMenu=[NSMenu new];
    [appMenu addItemWithTitle:@"About QOL Score · Ajito" action:@selector(about) keyEquivalent:@""];
    [appMenu addItem:NSMenuItem.separatorItem];[appMenu addItemWithTitle:@"Quit QOL Score" action:@selector(terminate:) keyEquivalent:@"q"];appItem.submenu=appMenu;
    NSMenuItem *editItem=[NSMenuItem new];[menu addItem:editItem];NSMenu *edit=[NSMenu new];edit.title=@"Edit";
    for(NSArray *row in @[@[@"Undo",@"undo:",@"z"],@[@"Redo",@"redo:",@"Z"],@[@"Cut",@"cut:",@"x"],@[@"Copy",@"copy:",@"c"],@[@"Paste",@"paste:",@"v"],@[@"Select All",@"selectAll:",@"a"]]) [edit addItemWithTitle:row[0] action:NSSelectorFromString(row[1]) keyEquivalent:row[2]];
    editItem.submenu=edit;NSMenuItem *viewItem=[NSMenuItem new];[menu addItem:viewItem];NSMenu *view=[NSMenu new];view.title=@"View";[view addItemWithTitle:@"Reload Interface" action:@selector(reloadInterface) keyEquivalent:@"r"];viewItem.submenu=view;NSApp.mainMenu=menu;
    NSRect screen=NSScreen.mainScreen.visibleFrame;
    self.window=[[NSWindow alloc] initWithContentRect:NSMakeRect(0,0,MIN(1380,screen.size.width-45),MIN(950,screen.size.height-45)) styleMask:NSWindowStyleMaskTitled|NSWindowStyleMaskClosable|NSWindowStyleMaskMiniaturizable|NSWindowStyleMaskResizable backing:NSBackingStoreBuffered defer:NO];
    self.window.delegate=self;self.window.title=@"QOL Score · Boyacky's Ajito";self.window.minSize=NSMakeSize(760,650);self.window.titlebarAppearsTransparent=YES;self.window.backgroundColor=[NSColor colorWithCalibratedRed:.063 green:.1 blue:.075 alpha:1];self.window.releasedWhenClosed=NO;[self.window center];
    WKWebViewConfiguration *config=[WKWebViewConfiguration new];config.websiteDataStore=WKWebsiteDataStore.nonPersistentDataStore;[config.userContentController addScriptMessageHandler:self name:@"exportInvitation"];[config.userContentController addScriptMessageHandler:self name:@"exportCSV"];[config.userContentController addScriptMessageHandler:self name:@"operationState"];
    self.web=[[WKWebView alloc] initWithFrame:NSZeroRect configuration:config];self.web.navigationDelegate=self;self.web.UIDelegate=self;[self.web setValue:@NO forKey:@"drawsBackground"];
    self.window.contentView=self.web;[self.window makeKeyAndOrderFront:nil];[NSApp activateIgnoringOtherApps:YES];
    [self.web loadHTMLString:@"<html style='background:#101913;color:#deddb9;font:16px -apple-system'><body style='display:grid;place-items:center;height:95vh'><div><h1>ボヤッキーのアジト</h1><p>Powering up the hideout…</p></div></body></html>" baseURL:nil];
    [self startBackend];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,25*NSEC_PER_SEC),dispatch_get_main_queue(),^{if(!self.ready&&!self.quitting)[self fail:@"The local engine did not start within 25 seconds. See ~/Library/Application Support/QOL Score/ajito-error.log for details."];});
}
- (void)startBackend {
    NSURL *root=NSBundle.mainBundle.resourceURL;NSTask *task=[NSTask new];task.executableURL=[root URLByAppendingPathComponent:@"backend/QOLService"];
    NSMutableArray *args=[@[@"--parent",[NSString stringWithFormat:@"%d",NSProcessInfo.processInfo.processIdentifier]] mutableCopy];
    if([NSProcessInfo.processInfo.arguments containsObject:@"--demo"]||[self argument:@"--smoke-test"])[args addObject:@"--demo"];task.arguments=args;
    NSPipe *pipe=[NSPipe pipe];task.standardOutput=pipe;
    NSURL *support=[NSFileManager.defaultManager.homeDirectoryForCurrentUser URLByAppendingPathComponent:@"Library/Application Support/QOL Score"];
    NSError *error=nil;[NSFileManager.defaultManager createDirectoryAtURL:support withIntermediateDirectories:YES attributes:nil error:&error];
    if(error){[self fail:error.localizedDescription];return;}
    NSString *log=[[support URLByAppendingPathComponent:@"ajito-error.log"] path];
    if(![NSFileManager.defaultManager fileExistsAtPath:log])[NSFileManager.defaultManager createFileAtPath:log contents:nil attributes:@{NSFilePosixPermissions:@0600}];
    task.standardError=[NSFileHandle fileHandleForWritingAtPath:log];
    __weak Ajito *weakSelf=self;
    task.terminationHandler=^(NSTask *p){dispatch_async(dispatch_get_main_queue(),^{Ajito *s=weakSelf;if(s&&!s.quitting)[s fail:[NSString stringWithFormat:@"The local engine stopped (code %d). Reopen QOL Score to reconnect. Your saved Notion entries are safe.",p.terminationStatus]];});};
    if(![task launchAndReturnError:&error]){[self fail:error.localizedDescription];return;}self.backend=task;
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_USER_INITIATED,0),^{
        NSMutableData *line=[NSMutableData data];
        @try { while(line.length<8192){NSData *part=[pipe.fileHandleForReading readDataOfLength:1];if(part.length==0||((const char *)part.bytes)[0]=='\n')break;[line appendData:part];} } @catch(NSException *exception) {}
        NSDictionary *json=[NSJSONSerialization JSONObjectWithData:line options:0 error:nil];NSURL *url=[json isKindOfClass:NSDictionary.class]?[NSURL URLWithString:json[@"url"]]:nil;
        dispatch_async(dispatch_get_main_queue(),^{if(self.quitting)return;if(![url.host isEqualToString:@"127.0.0.1"]){[self fail:@"The local engine could not initialize. Check ajito-error.log in your QOL Score support folder."];return;}self.localURL=url;self.ready=YES;[self.web loadRequest:[NSURLRequest requestWithURL:url]];});
    });
}
- (void)reloadInterface {if(self.localURL)[self.web loadRequest:[NSURLRequest requestWithURL:self.localURL]];}
- (void)about {NSAlert *a=[NSAlert new];a.messageText=@"QOL Score · Boyacky's Ajito";a.informativeText=@"Version 2.0.2\nA little hideout for better days.\nSame scoring model and Notion backend.\nFan-inspired Yatterman / Doronbo theme.";[a runModal];}
- (void)fail:(NSString *)message {
    if(self.quitting)return;
    if(self.smokePath){[self finishSmoke:@{@"ok":@NO,@"error":message}];return;}
    NSAlert *a=[NSAlert new];a.messageText=@"The hideout needs a quick repair";a.informativeText=message;a.alertStyle=NSAlertStyleWarning;[a addButtonWithTitle:@"Quit"];[a runModal];[NSApp terminate:nil];
}
- (void)webView:(WKWebView *)web decidePolicyForNavigationAction:(WKNavigationAction *)action decisionHandler:(void (^)(WKNavigationActionPolicy))decision {
    NSURL *url=action.request.URL;
    if([url.scheme isEqualToString:@"about"]||([url.host isEqualToString:@"127.0.0.1"]&&[url.port isEqual:self.localURL.port])){decision(WKNavigationActionPolicyAllow);return;}
    if(([@[@"http",@"https"] containsObject:url.scheme])&&action.navigationType==WKNavigationTypeLinkActivated)[NSWorkspace.sharedWorkspace openURL:url];decision(WKNavigationActionPolicyCancel);
}
- (void)webView:(WKWebView *)web didFailProvisionalNavigation:(WKNavigation *)navigation withError:(NSError *)error {if(error.code!=NSURLErrorCancelled)[self fail:[@"The interface could not load: " stringByAppendingString:error.localizedDescription]];}
- (void)userContentController:(WKUserContentController *)controller didReceiveScriptMessage:(WKScriptMessage *)message {
    if([message.name isEqualToString:@"operationState"] && message.frameInfo.mainFrame && [message.frameInfo.securityOrigin.host isEqualToString:@"127.0.0.1"]){self.operationBusy=[message.body boolValue];return;}
    if(!([message.name isEqualToString:@"exportInvitation"]||[message.name isEqualToString:@"exportCSV"])||!message.frameInfo.mainFrame||![message.frameInfo.securityOrigin.host isEqualToString:@"127.0.0.1"]||![message.body isKindOfClass:NSString.class])return;
    NSSavePanel *panel=[NSSavePanel savePanel];BOOL csv=[message.name isEqualToString:@"exportCSV"];panel.nameFieldStringValue=csv?@"QOL-scores.csv":@"QOL-Friends.qol-group.json";panel.allowedContentTypes=csv?@[UTTypeCommaSeparatedText]:@[UTTypeJSON];
    [panel beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse response){if(response==NSModalResponseOK){NSError *error=nil;[message.body writeToURL:panel.URL atomically:YES encoding:NSUTF8StringEncoding error:&error];if(error)[self fail:error.localizedDescription];}}];
}
- (void)webView:(WKWebView *)web runOpenPanelWithParameters:(WKOpenPanelParameters *)parameters initiatedByFrame:(WKFrameInfo *)frame completionHandler:(void (^)(NSArray<NSURL *> *))completion {
    NSOpenPanel *p=[NSOpenPanel openPanel];p.allowsMultipleSelection=NO;p.canChooseDirectories=NO;p.allowedContentTypes=@[UTTypeJSON];[p beginSheetModalForWindow:self.window completionHandler:^(NSModalResponse response){completion(response==NSModalResponseOK?p.URLs:nil);}];
}
- (void)webView:(WKWebView *)web didFinishNavigation:(WKNavigation *)navigation {
    if(![web.URL.host isEqualToString:@"127.0.0.1"]||!self.smokePath)return;
    NSString *source=[NSString stringWithContentsOfURL:[NSBundle.mainBundle.resourceURL URLByAppendingPathComponent:([self argument:@"--read-check"]?@"read-check.js":([self argument:@"--setup-check"]?@"setup-check.js":@"smoke.js"))] encoding:NSUTF8StringEncoding error:nil];
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC),dispatch_get_main_queue(),^{
        [self.web callAsyncJavaScript:source arguments:@{} inFrame:nil inContentWorld:WKContentWorld.pageWorld completionHandler:^(id result,NSError *error){
            NSDictionary *report=error?@{@"ok":@NO,@"error":error.localizedDescription}:([result isKindOfClass:NSDictionary.class]?result:@{@"ok":@NO,@"error":@"Empty smoke report"});
            if(self.screenshotPath){[self.web takeSnapshotWithConfiguration:nil completionHandler:^(NSImage *image,NSError *error){if(image){NSBitmapImageRep *bitmap=[NSBitmapImageRep imageRepWithData:image.TIFFRepresentation];[[bitmap representationUsingType:NSBitmapImageFileTypePNG properties:@{}] writeToFile:self.screenshotPath atomically:YES];}[self finishSmoke:report];}];}else [self finishSmoke:report];
        }];
    });
}
- (void)finishSmoke:(NSDictionary *)report {NSData *data=[NSJSONSerialization dataWithJSONObject:report options:NSJSONWritingPrettyPrinted|NSJSONWritingSortedKeys error:nil];[data writeToFile:self.smokePath atomically:YES];[NSApp terminate:nil];}
- (BOOL)confirmClose {
    if(!self.operationBusy)return YES;
    NSAlert *a=[NSAlert new];a.messageText=@"A Notion request is still running";a.informativeText=@"Keep the window open until it finishes. If you quit during a save, check Notion before submitting again.";[a addButtonWithTitle:@"Keep open"];[a addButtonWithTitle:@"Quit anyway"];BOOL allow=[a runModal]==NSAlertSecondButtonReturn;if(allow)self.operationBusy=NO;return allow;
}
- (BOOL)windowShouldClose:(NSWindow *)sender { return [self confirmClose]; }
- (NSApplicationTerminateReply)applicationShouldTerminate:(NSApplication *)sender { return self.quitting||[self confirmClose]?NSTerminateNow:NSTerminateCancel; }
- (BOOL)applicationShouldTerminateAfterLastWindowClosed:(NSApplication *)sender {return YES;}
- (void)applicationWillTerminate:(NSNotification *)notification {self.quitting=YES;if(self.backend.running)[self.backend terminate];}
@end
int main(int argc,const char *argv[]){@autoreleasepool{NSApplication *app=NSApplication.sharedApplication;Ajito *delegate=[Ajito new];app.delegate=delegate;[app setActivationPolicy:NSApplicationActivationPolicyRegular];[app run];}return 0;}
