from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
506258
507371
507367
507444
462240
504291
504311
504444
505734
471887
501734
502768
502964
500533
500559
500562
500678
500685
500700
501113
501121
498461
314904
475612
496923
431896
432590
104307
481044
477910
477829
403105
477384
471040
475451
474610
465714
465716
469737
469959
469966
470910
322626
324075
429560
463814
463820
463822
465789
455877
465819
465860
465065
461806
461411
457281
446276
444530
441909
441910
441911
458801
457146
459025
459030
459041
459056
459074
455458
456937
456985
396732
452839
455032
454816
211700
446025
455025
449316
453087
395821
322549
278008
422828
451393
452829
419639
452514
447206
448137
444064
443813
443816
446022
446023
446030
446080
440577
377178
439122
441609
441622
443546
443589
441659
441901
441914
441709
440085
434531
434805
433903
433651
429343
358848
363672
418481
428360
428376
387848
428629
429087
429111
427111
423511
421055
422075
398750
422854
406360
420336
418955
241601
415791
399706
412921
408794
409654
374061
349488
386873
403876
399834
322373
404378
335442
402655
402658
402676
402686
400412
401478
400030
400027
400024
400016
399993
397183
399712
400390
399730
397770
391364
391365
62093
390353
314094
389999
387590
384189
384027
386948
386600
386715
386798
386745
308898
374213
334930
198027
324686
345399
282269
333046
339981
339441
334073
330541
228094
323313
208655
309279
318496
229730
306426
306766
230951
302092
279371
229331




'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
